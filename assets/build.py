#!/usr/bin/env python3
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CINZEL = open(os.path.join(HERE, 'font_cinzel.b64')).read().strip()
EBG    = open(os.path.join(HERE, 'font_ebg.b64')).read().strip()

BG     = '#0B0B0E'
LINE   = '#232329'
LINE2  = '#33333B'
IVORY  = '#DBD7CE'
GRAY   = '#8A8F98'
DIM    = '#55585F'
RED    = '#B0413E'

MONO = "'Cascadia Code','SF Mono','Fira Code',Consolas,'Courier New',monospace"
SANS = "'Segoe UI',system-ui,-apple-system,sans-serif"

def style(cinzel=True, ebg=False, extra=''):
    css = ''
    if cinzel:
        css += "@font-face{font-family:'CZ';src:url(data:font/woff2;base64,%s) format('woff2');}\n" % CINZEL
        css += ".cz{font-family:'CZ',Georgia,serif;font-weight:600}\n"
    if ebg:
        css += "@font-face{font-family:'EBG';src:url(data:font/woff2;base64,%s) format('woff2');font-style:italic}\n" % EBG
        css += ".ebg{font-family:'EBG',Georgia,serif;font-style:italic}\n"
    css += ".mono{font-family:%s}\n.sans{font-family:%s}\n" % (MONO, SANS)
    css += extra
    return '<style>' + css + '</style>'

def diamond(x, y, s=3.2, color=RED, opacity='.9'):
    return f'<path d="M{x},{y-s} L{x+s},{y} L{x},{y+s} L{x-s},{y} Z" fill="{color}" fill-opacity="{opacity}"/>'

def corners(w, h, m=14, l=12, color=LINE2):
    p = []
    for cx, cy, dx, dy in [(m,m,1,1),(w-m,m,-1,1),(m,h-m,1,-1),(w-m,h-m,-1,-1)]:
        p.append(f'<path d="M{cx+dx*l},{cy} L{cx},{cy} L{cx},{cy+dy*l}" stroke="{color}" stroke-width="1" fill="none"/>')
    return '\n'.join(p)

def moons(cx, y, r=5.5, gap=26):
    xs = [cx - 2*gap, cx - gap, cx, cx + gap, cx + 2*gap]
    out = f'''<defs>
<mask id="mR"><rect x="-20" y="-20" width="40" height="40" fill="#000"/><rect x="0" y="-20" width="20" height="40" fill="#fff"/></mask>
<mask id="mL"><rect x="-20" y="-20" width="40" height="40" fill="#000"/><rect x="-20" y="-20" width="20" height="40" fill="#fff"/></mask>
</defs>'''
    out += f'<circle cx="{xs[0]}" cy="{y}" r="{r}" fill="none" stroke="{DIM}" stroke-width="1"/>'
    out += f'<g transform="translate({xs[1]},{y})"><circle r="{r}" fill="none" stroke="{DIM}" stroke-width="1"/><circle r="{r}" fill="{DIM}" mask="url(#mR)"/></g>'
    out += f'<circle cx="{xs[2]}" cy="{y}" r="{r}" fill="{GRAY}"/>'
    out += f'<g transform="translate({xs[3]},{y})"><circle r="{r}" fill="none" stroke="{DIM}" stroke-width="1"/><circle r="{r}" fill="{DIM}" mask="url(#mL)"/></g>'
    out += f'<circle cx="{xs[4]}" cy="{y}" r="{r}" fill="none" stroke="{DIM}" stroke-width="1"/>'
    return out


def header():
    W, H = 880, 300
    anims = '''
@keyframes tw{0%,100%{opacity:.06}50%{opacity:.7}}
.tw{animation:tw 4s ease-in-out infinite}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.spin{animation:spin 90s linear infinite;transform-origin:440px 150px}
.spin2{animation:spin 140s linear infinite reverse;transform-origin:440px 150px}
@keyframes br{0%,100%{opacity:.5}50%{opacity:1}}
.br{animation:br 6s ease-in-out infinite}
'''
    stars = ''
    pts = [(90,60,0.0),(150,210,1.3),(230,90,2.6),(310,240,0.7),(200,160,3.1),(120,130,1.9),
           (560,230,0.4),(640,80,1.6),(700,190,2.9),(760,60,0.9),(810,230,2.2),(680,140,3.4),
           (390,50,1.1),(500,60,2.4),(300,40,3.7),(590,45,0.2),(80,260,2.0),(800,120,1.4)]
    for x, y, d in pts:
        stars += f'<circle cx="{x}" cy="{y}" r="1" fill="{GRAY}" class="tw" style="animation-delay:{d}s"/>\n'

    ticks = ''
    for i in range(72):
        ticks += f'<line x1="0" y1="-124" x2="0" y2="{-120 if i % 6 else -114}" stroke="{LINE2}" stroke-width="1" transform="rotate({i*5})"/>\n'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{style(cinzel=True, extra=anims)}
<defs>
<radialGradient id="vig" cx=".5" cy=".5" r=".75">
<stop offset="0" stop-color="#131318"/><stop offset=".65" stop-color="{BG}"/><stop offset="1" stop-color="#08080A"/>
</radialGradient>
<clipPath id="panel"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6"/></clipPath>
</defs>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="url(#vig)"/>
<g clip-path="url(#panel)">
{stars}
<g class="spin"><g transform="translate(440,150)">
<circle r="124" fill="none" stroke="{LINE2}" stroke-width="1" stroke-dasharray="1 7"/>
{ticks}
</g></g>
<g class="spin2"><g transform="translate(440,150)">
<circle r="104" fill="none" stroke="{LINE2}" stroke-width="1"/>
<rect x="-104" y="-104" width="208" height="208" fill="none" stroke="{LINE2}" stroke-width="1" transform="rotate(45)" opacity=".55"/>
<rect x="-104" y="-104" width="208" height="208" fill="none" stroke="{LINE2}" stroke-width="1" opacity=".35"/>
</g></g>
<circle cx="440" cy="150" r="88" fill="{BG}" opacity=".82"/>
</g>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="none" stroke="{LINE}" stroke-width="1.5"/>
<rect x="11" y="11" width="{W-22}" height="{H-22}" fill="none" stroke="{LINE}" stroke-width="1" opacity=".6"/>
{corners(W, H, 22, 14)}

<line x1="330" y1="96" x2="550" y2="96" stroke="{LINE2}" stroke-width="1"/>
<text x="440" y="172" text-anchor="middle" class="cz" font-size="44" letter-spacing="14" fill="{IVORY}">ENERYLEEN</text>
<g class="br">{moons(440, 232)}</g>
</svg>'''


def sign(title):
    tw = len(title) * 24
    lx1, lx2 = 440 - tw//2 - 60, 440 - tw//2 - 16
    rx1, rx2 = 440 + tw//2 + 16, 440 + tw//2 + 60
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="56" viewBox="0 0 880 56">
{style()}
<rect x=".5" y=".5" width="879" height="55" rx="6" fill="{BG}" stroke="{LINE}"/>
{corners(880, 56, 10, 8)}
<line x1="{lx1}" y1="28" x2="{lx2}" y2="28" stroke="{LINE2}" stroke-width="1"/>
<line x1="{rx1}" y1="28" x2="{rx2}" y2="28" stroke="{LINE2}" stroke-width="1"/>
{diamond(lx2 + 8, 28, 2.6)}
{diamond(rx1 - 8, 28, 2.6)}
<text x="440" y="34" text-anchor="middle" class="cz" font-size="17" letter-spacing="9" fill="{IVORY}">{title}</text>
</svg>'''


ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI']

def card(name, desc1, desc2, lang, num, stars=0):
    star = f'<text x="404" y="39" text-anchor="end" class="mono" font-size="12" fill="{GRAY}">★ {stars}</text>' if stars else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="432" height="140" viewBox="0 0 432 140">
{style()}
<rect x=".5" y=".5" width="431" height="139" rx="6" fill="{BG}" stroke="{LINE}"/>
{corners(432, 140, 11, 9)}
<text x="28" y="40" class="mono" font-weight="700" font-size="16" fill="{IVORY}">{name}</text>
{star}
<text x="28" y="68" class="sans" font-size="13" fill="{GRAY}">{desc1}</text>
<text x="28" y="87" class="sans" font-size="13" fill="{GRAY}">{desc2}</text>
<circle cx="32" cy="111" r="3.5" fill="none" stroke="{DIM}" stroke-width="1.2"/>
<text x="44" y="115" class="mono" font-size="11.5" letter-spacing="1" fill="{DIM}">{lang}</text>
<text x="404" y="116" text-anchor="end" class="cz" font-size="13" letter-spacing="2" fill="{RED}" fill-opacity=".85">{num}.</text>
</svg>'''

def card_more():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="432" height="140" viewBox="0 0 432 140">
{style(ebg=True)}
<rect x=".5" y=".5" width="431" height="139" rx="6" fill="{BG}" stroke="{LINE}" stroke-dasharray="5 6"/>
{diamond(216, 56, 3, DIM)}
<text x="216" y="88" text-anchor="middle" class="ebg" font-size="15" letter-spacing="2" fill="{GRAY}">et cetera</text>
<text x="216" y="110" text-anchor="middle" class="mono" font-size="11" letter-spacing="2" fill="{DIM}">ALL REPOSITORIES →</text>
</svg>'''


def stack():
    rows = [
        ['TypeScript', 'JavaScript', 'Go', 'Python', 'Java', 'C#'],
        ['Node.js', 'React', 'PostgreSQL', 'Docker', 'Linux'],
    ]
    body = ''
    for r, items in enumerate(rows):
        y = 76 + r * 40
        widths = [len(s) * 8.3 for s in items]
        total = sum(widths) + 34 * (len(items) - 1)
        x = 440 - total / 2
        for i, (s, w) in enumerate(zip(items, widths)):
            body += f'<text x="{x:.0f}" y="{y}" class="mono" font-size="14" fill="#A9AEB8">{s.replace("&", "&amp;")}</text>\n'
            x += w
            if i < len(items) - 1:
                body += diamond(x + 17, y - 5, 2.4, RED, '.75') + '\n'
                x += 34
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="150" viewBox="0 0 880 150">
{style()}
<rect x=".5" y=".5" width="879" height="149" rx="6" fill="{BG}" stroke="{LINE}"/>
{corners(880, 150, 11, 9)}
<line x1="296" y1="36" x2="358" y2="36" stroke="{LINE2}" stroke-width="1"/>
<line x1="522" y1="36" x2="584" y2="36" stroke="{LINE2}" stroke-width="1"/>
{diamond(366, 36, 2.6)}
{diamond(514, 36, 2.6)}
<text x="440" y="42" text-anchor="middle" class="cz" font-size="17" letter-spacing="9" fill="{IVORY}">STACK</text>
{body}
</svg>'''


OUT = {
    'header.svg': header(),
    'sign-projects.svg': sign('PROJECTS'),
    'sign-stats.svg': sign('STATISTICS'),
    'stack.svg': stack(),
    'card-codex.svg': card('ai-web-design-codex', '60 cross-linked guides on web design —', 'for humans and AI agents', 'MARKDOWN', 'I', stars=4),
    'card-yandexrpc.svg': card('YandexRPC', 'Discord Rich Presence for Yandex Music —', 'native Windows tray application', 'C# / .NET', 'II', stars=1),
    'card-damage.svg': card('damage-indicator', 'Floating damage numbers above hit', 'entities — NeoForge 1.21 mod', 'JAVA', 'III'),
    'card-adaptivejump.svg': card('adaptivejump-neoforge', 'Instant jump rebound on landing —', 'removes the post-jump cooldown', 'JAVA', 'IV'),
    'card-attack.svg': card('Attack-indicator', 'Configurable floating damage indicators', 'for Paper servers', 'JAVA', 'V'),
    'card-more.svg': card_more(),
}

import glob
for old in glob.glob(os.path.join(HERE, '*.svg')):
    os.remove(old)
for fname, svg in OUT.items():
    with open(os.path.join(HERE, fname), 'w') as f:
        f.write(svg)
    print(f'{fname}: {len(svg)//1024}K')
