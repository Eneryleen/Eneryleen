#!/bin/bash
# Ежедневное обновление статистики профиля: собрать данные → перерисовать SVG → закоммитить.
# Коммит идёт от служебного имени, не привязанного к аккаунту, — иначе сам скрипт
# каждый день добавлял бы «вклад» и рисовал бесконечную серию.
# DRY=1 — только пересобрать, без коммита, пуша и уведомлений. FORCE=1 — отключить защиту от просадки данных.
# О сбое сообщает в Telegram, если есть ~/.config/profile-refresh.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

notify() {
  echo "FAIL: $1"
  [ "${DRY:-}" = 1 ] && return 0
  [ -f "$HOME/.config/profile-refresh.env" ] || return 0
  . "$HOME/.config/profile-refresh.env"
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || return 0
  # Токен уходит через stdin, а не в аргументах — чтобы не светился в ps.
  printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$TELEGRAM_BOT_TOKEN" \
    | curl -s -m 20 --config - --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=GitHub profile refresh failed: $1" >/dev/null || true
}
trap 'notify "\"$BASH_COMMAND\" exited with $?"' ERR
trap 'notify "killed by signal (timeout?)"; exit 143' TERM

mkdir -p "$HOME/.cache"
exec 9>"$HOME/.cache/profile-refresh.lock"
flock -n 9 || { echo "another refresh is running"; exit 0; }
if [ -f refresh.log ] && [ "$(stat -c%s refresh.log)" -gt 1000000 ]; then : > refresh.log; fi

echo "== $(date -Is)"
# Чужие правки в рабочей копии не трогаем — иначе закоммитим их от имени бота.
dirty=$(git status --porcelain | grep -vE '^.. assets/(stats\.json|[^/]+\.svg)$' || true)
if [ -n "$dirty" ]; then notify "working tree has unrelated changes: $dirty"; exit 1; fi
git pull -q --ff-only
for step in assets/stats.py assets/build.py; do
  if ! out=$(python3 "$step" 2>&1); then
    printf '%s\n' "$out"
    notify "$step failed: $(printf '%s' "$out" | tail -c 400)"
    exit 1
  fi
  printf '%s\n' "$out" | tail -n 1
done
git add -A assets
if git diff --cached --quiet; then echo "no changes"; exit 0; fi
if [ "${DRY:-}" = 1 ]; then echo "dry run: skipping commit"; git restore --staged assets; exit 0; fi
git -c user.name='profile-stats' -c user.email='profile-stats@invalid' commit -q -m 'chore: refresh stats'
git push -q origin HEAD:master
echo "pushed"
