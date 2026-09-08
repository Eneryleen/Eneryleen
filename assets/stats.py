#!/usr/bin/env python3
"""Собирает статистику аккаунта через GitHub GraphQL (gh api) в stats.json.

Нужен авторизованный `gh` с правом repo — тогда видны и приватные репозитории.
Порядок: python3 assets/stats.py && python3 assets/build.py

Защита: если данных стало подозрительно меньше, чем в прошлом stats.json (0 приватных
репо, просадка >25 %), файл не перезаписывается — скорее всего токен потерял доступ.
FORCE=1 отключает эту проверку.

Известная особенность GitHub: календарь вкладов изредка пересчитывается со сдвигом
суточной границы (суммы те же, отдельные дни ±1), поэтому тепловая карта и даты серий
могут «дрожать» между запусками — это не ошибка скрипта.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'stats.json')

# Репозитории с темой profile-ignore (снимки чужого кода: вендор, декомпилят, форк без метки)
# в подсчёты не идут — иначе чужой PHP «съедает» треть диаграммы языков.
# Тема ставится в настройках репо: gh repo edit <owner>/<name> --add-topic profile-ignore
SKIP_TOPIC = 'profile-ignore'
TOP_LANGS = 6
PAGE = 15        # больше — GitHub отвечает 502 на подсчёте истории коммитов
MIN_PAGE = 3
TIMEOUT = 120    # секунд на один запрос к gh
MAX_DROP = 0.25  # допустимая просадка ключевых чисел между запусками


class Fatal(RuntimeError):
    """Повторять бессмысленно — нужно вмешательство."""


def run_gh(*args):
    return subprocess.run(['gh', *args], capture_output=True, text=True, timeout=TIMEOUT)


def check_scopes():
    p = run_gh('api', '-i', 'user')
    if p.returncode != 0:
        raise Fatal('gh api user failed: ' + p.stderr.strip()[:200])
    header = next((l.split(':', 1)[1] for l in p.stdout.splitlines()
                   if l.lower().startswith('x-oauth-scopes:')), None)
    # У fine-grained токенов заголовка нет — тогда полагаемся на проверку данных ниже.
    if header is not None and 'repo' not in [s.strip() for s in header.split(',')]:
        raise Fatal(f'gh token lacks the "repo" scope (has: {header.strip() or "none"}); private repos would be invisible')


def gql(query, **variables):
    args = ['api', 'graphql', '-f', 'query=' + query]
    for k, v in variables.items():
        args += ['-f', f'{k}={v}']
    last = ''
    for attempt in range(4):
        try:
            p = run_gh(*args)
        except subprocess.TimeoutExpired:
            last = f'no answer in {TIMEOUT}s'
        else:
            try:
                body = json.loads(p.stdout) if p.stdout.strip() else {}
            except ValueError:
                body = {}
            errors = body.get('errors') or []
            if any(e.get('type') == 'RATE_LIMITED' for e in errors):
                raise Fatal('GitHub GraphQL rate limit hit — retry later')
            if p.returncode == 0 and body.get('data') and not errors:
                return body['data']
            last = (errors[0].get('message', '') if errors else p.stderr.strip())[:200]
        print(f'gh api failed (try {attempt + 1}): {last}', file=sys.stderr)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'GraphQL request failed after retries: {last}')


def fetch_viewer():
    d = gql('query { viewer { id login createdAt contributionsCollection { contributionYears '
            'contributionCalendar { totalContributions weeks { contributionDays { date weekday contributionCount } } } } } }')
    return d['viewer']


def fetch_year_totals(years):
    parts = [f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{y}-12-31T23:59:59Z")'
             '{ contributionCalendar { totalContributions } }' for y in years]
    d = gql('query { viewer { ' + ' '.join(parts) + ' } }')
    return {int(k[1:]): v['contributionCalendar']['totalContributions'] for k, v in d['viewer'].items()}


def repos_query(page):
    return '''query($after:String,$uid:ID){ viewer { repositories(first:%d, after:$after, ownerAffiliations:[OWNER],
      orderBy:{field:PUSHED_AT,direction:DESC}) { pageInfo{hasNextPage endCursor} nodes {
      name isPrivate isFork isArchived stargazerCount primaryLanguage{name}
      repositoryTopics(first:20){ nodes{ topic{name} } }
      languages(first:10,orderBy:{field:SIZE,direction:DESC}){ totalSize edges{ size node{name} } }
      defaultBranchRef{ target{ ... on Commit { history(author:{id:$uid}){ totalCount } } } } } } } }''' % page


def fetch_repos(uid):
    after, repos, page = None, [], PAGE
    while True:
        variables = {'uid': uid}
        if after:
            variables['after'] = after
        try:
            rr = gql(repos_query(page), **variables)['viewer']['repositories']
        except Fatal:
            raise
        except RuntimeError:
            # Тяжёлая страница (таймаут на истории коммитов) — пробуем мельче, не повторяя то же самое.
            if page <= MIN_PAGE:
                raise
            page = max(MIN_PAGE, page // 3)
            print(f'retrying with page size {page}', file=sys.stderr)
            continue
        repos += rr['nodes']
        if not rr['pageInfo']['hasNextPage']:
            return repos
        after = rr['pageInfo']['endCursor']


def streaks(days):
    """days — список {date, count} по возрастанию даты. При равной длине берётся более свежая серия."""
    longest, cur, start = 0, 0, None
    best = (None, None)
    for d in days:
        if d['count'] > 0:
            cur += 1
            start = start or d['date']
            if cur >= longest:
                longest, best = cur, (start, d['date'])
        else:
            cur, start = 0, None
    # Сегодняшний пустой день серию не рвёт — день ещё не кончился.
    tail = days[:-1] if days and days[-1]['count'] == 0 else days
    current = 0
    for d in reversed(tail):
        if d['count'] > 0:
            current += 1
        else:
            break
    return current, longest, best


def sanity(new):
    if new['repos']['private'] == 0:
        raise Fatal('API shows 0 private repositories — token lost access? refusing to overwrite stats.json')
    if sum(len(w) for w in new['calendar']) < 360 or not new['languages']:
        raise Fatal('calendar or languages came back truncated; refusing to overwrite stats.json')
    if not os.path.exists(OUT):
        return
    old = json.load(open(OUT))
    checks = [('repos.total', old['repos']['total'], new['repos']['total']),
              ('commits', old['commits'], new['commits']),
              ('contributions.last_year', old['contributions']['last_year'], new['contributions']['last_year'])]
    for name, o, n in checks:
        if o and n < o * (1 - MAX_DROP):
            raise Fatal(f'{name} dropped {o} -> {n}; refusing to overwrite stats.json (FORCE=1 to override)')


def main():
    check_scopes()
    viewer = fetch_viewer()
    cal = viewer['contributionsCollection']['contributionCalendar']
    weeks = [[{'date': d['date'], 'weekday': d['weekday'], 'count': d['contributionCount']}
              for d in w['contributionDays']] for w in cal['weeks']]
    current, longest, best = streaks([d for w in weeks for d in w])

    years = sorted(viewer['contributionsCollection']['contributionYears'])
    per_year = fetch_year_totals(years)

    repos = fetch_repos(viewer['id'])
    own = [r for r in repos if not r['isFork']]

    def counted(r):
        topics = {n['topic']['name'] for n in r['repositoryTopics']['nodes']}
        return not r['isArchived'] and SKIP_TOPIC not in topics and r['name'] != viewer['login']

    kept = [r for r in own if counted(r)]
    commits = sum(((r['defaultBranchRef'] or {}).get('target') or {}).get('history', {}).get('totalCount', 0)
                  for r in kept)

    lang_bytes = Counter()
    for r in kept:
        for e in r['languages']['edges']:
            lang_bytes[e['node']['name']] += e['size']
    total = sum(lang_bytes.values()) or 1
    languages = [{'name': n, 'pct': round(b * 100 / total, 1)} for n, b in lang_bytes.most_common(TOP_LANGS)]
    other = round(100 - sum(l['pct'] for l in languages), 1)
    if other >= 0.1 and len(lang_bytes) > TOP_LANGS:
        languages.append({'name': 'Other', 'pct': other})

    stats = {
        'refreshed': dt.date.today().isoformat(),
        'login': viewer['login'],
        'created_at': viewer['createdAt'][:10],
        # Все счётчики — по одному и тому же набору: свои, не форки, не архив, без profile-ignore.
        'repos': {
            'total': len(kept),
            'private': sum(r['isPrivate'] for r in kept),
            'public': sum(not r['isPrivate'] for r in kept),
            'by_primary': dict(Counter(r['primaryLanguage']['name'] for r in kept if r['primaryLanguage']).most_common()),
        },
        'stars': sum(r['stargazerCount'] for r in kept if not r['isPrivate']),
        'commits': commits,
        'contributions': {
            'last_year': cal['totalContributions'],
            'this_year': per_year.get(dt.date.today().year, 0),
            'all_time': sum(per_year.values()),
            'per_year': per_year,
            'current_streak': current,
            'longest_streak': longest,
            'longest_range': list(best),
        },
        'languages': languages,
        'public_repos': [{'name': r['name'], 'stars': r['stargazerCount']} for r in kept if not r['isPrivate']],
        'calendar': weeks,
    }
    if os.environ.get('FORCE') != '1':
        sanity(stats)
    tmp = OUT + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(stats, f, indent=1, ensure_ascii=False)
    os.replace(tmp, OUT)
    c = stats['contributions']
    print(f"repos {stats['repos']['total']} ({stats['repos']['private']} private), commits {commits}, "
          f"stars {stats['stars']}, contributions {c['last_year']}/12mo, streak {current}/{longest} {best}, "
          f"langs {[(l['name'], l['pct']) for l in languages]}")


if __name__ == '__main__':
    try:
        main()
    except Fatal as e:
        sys.exit(f'FATAL: {e}')
