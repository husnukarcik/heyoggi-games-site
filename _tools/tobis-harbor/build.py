#!/usr/bin/env python3
"""Tobi's Harbor destek, gizlilik ve veri silme sayfalarını oyunun 10 dilinde üretir.

Kaynaklar: i18n/privacy.<dil>.md (gizlilik politikası; en ve tr oyunun deposundaki docs/legal ile aynı),
i18n/support.<dil>.json (destek sayfası), app_labels.json (oyundaki menü adları, Strings.csv'den).
Çıktı: depo kökünde tobis-harbor/ (İngilizce; Play Console'daki adres değişmesin) ve tobis-harbor/<dil>/.
Ayrıca tobisharbor/ → tobis-harbor/ yönlendirmesi. Çalıştırma: python3 _tools/tobis-harbor/build.py
"""
import html
import json
import re
from pathlib import Path

import md2html  # oyunun deposundaki tools/legal/privacy_html.py'nin kopyası (convert)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / 'tobis-harbor'
SITE = 'https://games.heyoggi.com'
EMAIL = 'heyoggi.games@gmail.com'
# Oyundaki dil sırası (Strings.csv); İngilizce kökte
LANGS = ['en', 'tr', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'id']
PAGES = {'support': '', 'privacy': 'privacy/', 'delete': 'delete-data/'}

_inline = md2html.inline


def inline(s: str) -> str:
    # Tek yıldız: italik (çeviri notu); kalın ** önce işlenir
    s = _inline(s)
    return re.sub(r'(?<![*\w])\*(?!\*)(.+?)(?<!\*)\*(?![*\w])', r'<em>\1</em>', s)


md2html.inline = inline

CSS = """
:root{--bg:#f6efe3;--card:#fffaf2;--text:#1f2a33;--muted:#5d6b75;--line:#e4d7c3;--accent:#1f6f8b;--chip:#efe4d2;--th:#f1e6c8}
@media (prefers-color-scheme:dark){:root{--bg:#121a20;--card:#1a242c;--text:#eef2f4;--muted:#a3b1ba;--line:#2a3640;--accent:#5bb3cf;--chip:#22313b;--th:#22313b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 64px}
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
header{display:flex;align-items:center;gap:14px;min-width:0}
header>div{min-width:0}
header img{width:56px;height:56px;border-radius:14px;background:var(--chip)}
.name{font-size:1.7rem;font-weight:700;margin:0;line-height:1.2}
.by{color:var(--muted);font-size:.95rem;overflow-wrap:anywhere}
h1,h2.title{font-size:1.3rem;margin:.6rem 0 .4rem}
h2{font-size:1.05rem;margin:1.4rem 0 .3rem}
h3{font-size:1.02rem;margin:1.2rem 0 .3rem}
p.updated,.sub{color:var(--muted)}
em{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 22px 18px;margin:18px 0}
a{color:var(--accent)}
ul,ol{padding-inline-start:1.3rem}
li{margin:.3rem 0}
table{border-collapse:collapse;margin:1em 0;display:block;overflow-x:auto;max-width:100%}
td,th{border:1px solid var(--line);padding:.4em .6em;text-align:start;vertical-align:top}
th{background:var(--th)}
nav.pages{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 0}
nav.pages a{text-decoration:none;padding:6px 12px;border-radius:999px;background:var(--chip);color:var(--text);font-size:.93rem}
nav.pages a[aria-current]{background:var(--accent);color:var(--card)}
details.lang{position:relative;flex:none;margin-top:8px}
details.lang summary{cursor:pointer;list-style:none;padding:6px 12px;border:1px solid var(--line);border-radius:10px;background:var(--card);font-size:.93rem;white-space:nowrap}
details.lang summary::-webkit-details-marker{display:none}
details.lang ul{position:absolute;inset-inline-end:0;z-index:5;margin:6px 0 0;padding:6px;list-style:none;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.15);min-width:190px}
details.lang li{margin:0}
details.lang li a{display:block;padding:6px 10px;border-radius:8px;text-decoration:none;color:var(--text)}
details.lang li a:hover,details.lang li a[aria-current]{background:var(--chip)}
footer{color:var(--muted);font-size:.9rem;margin-top:40px}
"""


def base(lang: str) -> str:
    return '/tobis-harbor/' if lang == 'en' else f'/tobis-harbor/{lang.lower()}/'


def url(lang: str, page: str) -> str:
    return base(lang) + PAGES[page]


def fill(text: str, lang: str, t: dict, labels: dict) -> str:
    subject = t['mailSubjectSupport'].replace(' ', '%20')
    values = {
        'email': f'<a href="mailto:{EMAIL}?subject={html.escape(subject)}">{EMAIL}</a>',
        'privacyLink': f'<a href="{url(lang, "privacy")}">{html.escape(t["navPrivacy"])}</a>',
        **{k: f'<b>{html.escape(v)}</b>' for k, v in labels.items()},
    }

    def rep(m: re.Match) -> str:
        if m.group(1) not in values:
            raise KeyError(f'{lang}: bilinmeyen yer tutucu {{{m.group(1)}}}')
        return values[m.group(1)]

    return re.sub(r'\{(\w+)\}', rep, html.escape(text, quote=False).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>'))


def page(lang: str, kind: str, t: dict, labels: dict, all_t: dict, privacy_html: str) -> str:
    title = {'support': t['titleSupport'], 'privacy': t['titlePrivacy'], 'delete': t['titleDelete']}[kind]
    alternates = '\n'.join(f'<link rel="alternate" hreflang="{l}" href="{SITE}{url(l, kind)}">' for l in LANGS)
    alternates += f'\n<link rel="alternate" hreflang="x-default" href="{SITE}{url("en", kind)}">'
    langs = '\n'.join(
        f'<li><a href="{url(l, kind)}" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{html.escape(all_t[l]["langName"])}</a></li>'
        for l in LANGS
    )
    nav = ''.join(
        f'<a href="{url(lang, k)}"{" aria-current=\"page\"" if k == kind else ""}>{html.escape(t[n])}</a>'
        for k, n in (('support', 'navSupport'), ('privacy', 'navPrivacy'), ('delete', 'navDelete'))
    )
    f = lambda key: fill(t[key], lang, t, labels)
    if kind == 'support':
        qa = ''.join(f'<h3>{html.escape(t[f"q{i}"])}</h3><p>{f(f"a{i}")}</p>' for i in range(1, 4))
        body = f"""<p>{f('intro')}</p>
<div class="card">
<h2 class="title">{html.escape(t['supportH'])}</h2>
<p>{f('supportP')}</p>
<h2 class="title">{html.escape(t['faqH'])}</h2>
{qa}
</div>"""
    elif kind == 'delete':
        body = f"""<div class="card">
<h2 class="title">{html.escape(t['delH'])}</h2>
<p>{f('delIntro')}</p>
<h3>{html.escape(t['delStatsH'])}</h3>
<ol><li>{f('delStats1')}</li><li>{f('delStats2')}</li></ol>
<p>{f('delStopP')}</p>
<h3>{html.escape(t['delLocalH'])}</h3>
<p>{f('delLocalP')}</p>
<h3>{html.escape(t['delNoAppH'])}</h3>
<p>{f('delNoAppP')}</p>
</div>"""
    else:
        body = f'<div class="card">\n{privacy_html}\n</div>'

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(t['metaDescription'])}">
<link rel="icon" href="/tobis-harbor/icon.png">
<link rel="canonical" href="{SITE}{url(lang, kind)}">
{alternates}
<style>{CSS}</style>
</head>
<body>
<main>
<div class="top">
<header><img src="/tobis-harbor/icon.png" alt=""><div><div class="name">Tobi's Harbor</div><div class="by">{html.escape(t['by'])}</div></div></header>
<details class="lang"><summary aria-label="{html.escape(t['language'])}">🌐 {html.escape(t['langName'])} ▾</summary>
<ul>
{langs}
</ul></details>
</div>
<nav class="pages">{nav}</nav>
{body}
<footer>© 2026 HeyOggi Games · <a href="mailto:{EMAIL}">{EMAIL}</a></footer>
</main>
</body>
</html>
"""


REDIRECT = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Tobi's Harbor</title>
<meta http-equiv="refresh" content="0; url=/tobis-harbor/">
<link rel="canonical" href="https://games.heyoggi.com/tobis-harbor/"></head>
<body><p><a href="/tobis-harbor/">Tobi's Harbor</a></p></body></html>
"""


def main():
    labels = json.loads((HERE / 'app_labels.json').read_text(encoding='utf-8'))
    all_t = {l: json.loads((HERE / 'i18n' / f'support.{l}.json').read_text(encoding='utf-8')) for l in LANGS}
    for l, t in all_t.items():
        missing = [k for k in all_t['en'] if k not in t]
        if missing:
            raise SystemExit(f'{l}: eksik anahtarlar {missing}')
    n = 0
    for l in LANGS:
        _, privacy = md2html.convert((HERE / 'i18n' / f'privacy.{l}.md').read_text(encoding='utf-8'))
        for kind, sub in PAGES.items():
            d = OUT / ('' if l == 'en' else l.lower()) / sub
            d.mkdir(parents=True, exist_ok=True)
            (d / 'index.html').write_text(page(l, kind, all_t[l], labels[l], all_t, privacy), encoding='utf-8')
            n += 1
    r = ROOT / 'tobisharbor'
    r.mkdir(exist_ok=True)
    (r / 'index.html').write_text(REDIRECT, encoding='utf-8')
    print(f'{n} sayfa + yönlendirme yazıldı')


if __name__ == '__main__':
    main()
