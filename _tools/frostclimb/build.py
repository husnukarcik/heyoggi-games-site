#!/usr/bin/env python3
"""Frostclimb destek / gizlilik / hesap silme sayfalarını 12 dilde üretir.

Kaynaklar: i18n/<dil>.json (metinler), app_labels.json (oyundaki menü adları; jump deposundaki
locales/*.json'dan alınır). Çıktı: depo kökünde frostclimb/ (İngilizce) ve frostclimb/<dil>/.
Çalıştırma: python3 _tools/frostclimb/build.py  (depo kökünden ya da herhangi bir yerden)
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / 'frostclimb'
EMAIL = 'heyoggi.games@gmail.com'
GOOGLE_PARTNER = 'https://policies.google.com/technologies/partner-sites'
# Oyundaki dil sırası; İngilizce kökte durur (mağazalara verilen adresler değişmesin)
LANGS = ['en', 'tr', 'de', 'fr', 'es', 'pt-BR', 'ru', 'ja', 'ko', 'zh-Hans', 'ar', 'id']
RTL = {'ar'}
PAGES = {'support': '', 'privacy': 'privacy/', 'delete': 'delete-account/'}

CSS = """
:root{--bg:#f4f8fc;--card:#fff;--text:#1a2433;--muted:#5b6b80;--accent:#1d6fd1;--line:#dde6f0;--chip:#e8f0f9}
@media (prefers-color-scheme:dark){:root{--bg:#0b1422;--card:#122033;--text:#e6eef8;--muted:#9fb1c7;--accent:#7fc0ff;--line:#22344d;--chip:#1a2c44}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Noto Sans Arabic","Hiragino Sans","PingFang SC","Apple SD Gothic Neo",sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 64px}
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
header{display:flex;align-items:center;gap:14px;min-width:0}
header>div{min-width:0}
header img{width:56px;height:56px;border-radius:14px}
h1{font-size:1.7rem;margin:0;line-height:1.2}
h2{font-size:1.25rem;margin:.6rem 0 .4rem}
h3{font-size:1.02rem;margin:1.3rem 0 .3rem}
.by{color:var(--muted);font-size:.95rem;overflow-wrap:anywhere}
.sub{color:var(--muted);margin:0 0 1rem}
.note{color:var(--muted);font-size:.9rem;font-style:italic;margin:0 0 .6rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 22px 18px;margin:18px 0}
a{color:var(--accent)}
ul,ol{padding-inline-start:1.3rem}
li{margin:.3rem 0}
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


def slug(lang: str) -> str:
    return lang.lower()


def base(lang: str) -> str:
    return '/frostclimb/' if lang == 'en' else f'/frostclimb/{slug(lang)}/'


def url(lang: str, page: str) -> str:
    return base(lang) + PAGES[page]


def fill(text: str, lang: str, t: dict, labels: dict, subject: str | None = None) -> str:
    """Yer tutucuları doldurur. Metinler güvenilir kaynaktır (bizim çevirimiz); <b> etiketleri korunur."""
    mail = f'mailto:{EMAIL}' + (f'?subject={html.escape(subject).replace(" ", "%20")}' if subject else '')
    values = {
        'email': f'<a href="{mail}">{EMAIL}</a>',
        'deleteLink': f'<a href="{url(lang, "delete")}">{html.escape(t["navDelete"])}</a>',
        'googlePartner': f'<a href="{GOOGLE_PARTNER}">policies.google.com/technologies/partner-sites</a>',
        'date': html.escape(t['date']),
        **{k: f'<b>{html.escape(v)}</b>' for k, v in labels.items()},
    }

    def rep(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise KeyError(f'{lang}: bilinmeyen yer tutucu {{{key}}}')
        return values[key]

    out = re.sub(r'\{(\w+)\}', rep, text)
    # Sağdan sola dillerde menü yolu oku da sola bakar
    return out.replace('→', '←') if lang in RTL else out


def page(lang: str, kind: str, t: dict, labels: dict, all_t: dict) -> str:
    rtl = lang in RTL
    title = {'support': t['titleSupport'], 'privacy': t['titlePrivacy'], 'delete': t['titleDelete']}[kind]
    alternates = '\n'.join(f'<link rel="alternate" hreflang="{l}" href="https://games.heyoggi.com{url(l, kind)}">' for l in LANGS)
    alternates += f'\n<link rel="alternate" hreflang="x-default" href="https://games.heyoggi.com{url("en", kind)}">'
    langs = '\n'.join(
        f'<li><a href="{url(l, kind)}" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{html.escape(all_t[l]["langName"])}</a></li>'
        for l in LANGS
    )
    nav = ''.join(
        f'<a href="{url(lang, k)}"{" aria-current=\"page\"" if k == kind else ""}>{html.escape(t[n])}</a>'
        for k, n in (('support', 'navSupport'), ('privacy', 'navPrivacy'), ('delete', 'navDelete'))
    )
    note = f'<p class="note">{html.escape(t["translationNote"])}</p>' if lang != 'en' and kind != 'support' else ''
    f = lambda key, subject=None: fill(t[key], lang, t, labels, subject)

    if kind == 'support':
        qa = ''.join(f'<h3>{html.escape(t[f"q{i}"])}</h3><p>{f(f"a{i}")}</p>' for i in range(1, 5))
        body = f"""<p>{f('intro')}</p>
<div class="card">
<h2>{html.escape(t['supportH'])}</h2>
<p>{f('supportP', t['mailSubjectSupport'])}</p>
<h2>{html.escape(t['faqH'])}</h2>
{qa}
</div>"""
    elif kind == 'privacy':
        items = ''.join(f'<li>{f(f"c{i}")}</li>' for i in range(1, 7))
        sections = ''.join(
            f'<h3>{html.escape(t[h])}</h3><p>{f(p)}</p>'
            for h, p in (('h2', 'pAds'), ('h3', 'pProviders'), ('h4', 'pDevice'), ('h5', 'pRetention'), ('h6', 'pDelete'),
                         ('h7', 'pSecurity'), ('h8', 'pChildren'), ('h9', 'pRights'), ('h10', 'pChanges'), ('h11', 'pContact'))
        )
        body = f"""<div class="card">
<h2>{html.escape(t['privacyH'])}</h2>
{note}<p class="sub">{f('effective')}</p>
<p>{f('pIntro')}</p>
<h3>{html.escape(t['h1'])}</h3>
<ul>{items}</ul>
<p>{f('notCollected')}</p>
{sections}
</div>"""
    else:
        steps = ''.join(f'<li>{f(f"step{i}")}</li>' for i in range(1, 4))
        deleted = ''.join(f'<li>{f(f"del{i}")}</li>' for i in range(1, 4))
        body = f"""<div class="card">
<h2>{html.escape(t['deleteH'])}</h2>
{note}<h3>{html.escape(t['opt1H'])}</h3>
<ol>{steps}</ol>
<h3>{html.escape(t['opt2H'])}</h3>
<p>{f('opt2P', t['mailSubjectDelete'])}</p>
<h3>{html.escape(t['deletedH'])}</h3>
<ul>{deleted}</ul>
<h3>{html.escape(t['keptH'])}</h3>
<p>{f('keptP')}</p>
</div>"""

    return f"""<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(t['metaDescription'])}">
<link rel="icon" href="/frostclimb/icon.png">
<link rel="canonical" href="https://games.heyoggi.com{url(lang, kind)}">
{alternates}
<style>{CSS}</style>
</head>
<body>
<main>
<div class="top">
<header><img src="/frostclimb/icon.png" alt=""><div><h1>Frostclimb</h1><div class="by">{html.escape(t['by'])}</div></div></header>
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


def main():
    labels = json.loads((HERE / 'app_labels.json').read_text(encoding='utf-8'))
    all_t = {l: json.loads((HERE / 'i18n' / f'{l}.json').read_text(encoding='utf-8')) for l in LANGS}
    en_keys = list(all_t['en'])
    for l, t in all_t.items():
        missing = [k for k in en_keys if k not in t]
        if missing:
            raise SystemExit(f'{l}: eksik anahtarlar {missing}')
    written = 0
    for l in LANGS:
        for kind, sub in PAGES.items():
            d = OUT / ('' if l == 'en' else slug(l)) / sub
            d.mkdir(parents=True, exist_ok=True)
            (d / 'index.html').write_text(page(l, kind, all_t[l], labels[l], all_t), encoding='utf-8')
            written += 1
    print(f'{written} sayfa yazıldı')


if __name__ == '__main__':
    main()
