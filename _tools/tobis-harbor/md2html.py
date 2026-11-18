"""docs/legal/privacy-policy.<lang>.md -> privacy-policy.<lang>.html (single file, plain HTML, no scripts, no external
resources). Run after editing the markdown: python tools/legal/privacy_html.py

--site also writes Builds/Store/privacy-site/index.html (10.10.2026): the public page for the Play Console's privacy policy
URL, to be put on GitHub Pages by hand. One self-contained file: English first, the Turkish text below it in the same page,
a link between them at the top of each. Nothing is published by this tool."""
import html, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEGAL = os.path.normpath(os.path.join(HERE, "..", "..", "docs", "legal"))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "Builds", "Store", "privacy-site", "index.html"))
# the game's copies (TextAssets in AppConfig, shown by PrivacyPanel); PrivacyTextTests checks they match
GAME = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Project", "Settings", "Legal"))
DATED = ("Son güncelleme", "Last updated", "Yürürlük tarihi", "Effective date")

CSS = """body{font-family:Georgia,'Times New Roman',serif;max-width:46em;margin:2em auto;padding:0 1em;line-height:1.55;color:#222;background:#fbf8f1}
h1{font-size:1.7em;border-bottom:2px solid #c9a24a;padding-bottom:.2em}h2{font-size:1.2em;margin-top:1.6em;color:#4a260e}
table{border-collapse:collapse;margin:1em 0}td,th{border:1px solid #c9b78f;padding:.35em .6em;text-align:left;vertical-align:top}
th{background:#f1e6c8}code{background:#f1e6c8;padding:0 .25em}a{color:#1a5a8a}p.updated{color:#666}"""
SITE_CSS = CSS + """
nav.lang{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:.95em;margin:.4em 0 1.2em}
nav.lang a{display:inline-block;padding:.35em .8em;border:1px solid #c9a24a;border-radius:1em;text-decoration:none;background:#fff}
section+section{margin-top:3em;border-top:2px solid #c9a24a;padding-top:1em}
table{display:block;overflow-x:auto;max-width:100%}
@media (max-width:30em){body{margin:1em auto;font-size:1.02em}h1{font-size:1.4em}}"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\(([a-z0-9.\-]+\.[a-z]{2,}/[^\s)]*)\)", lambda m: '(<a href="https://%s">%s</a>)' % (m.group(1), m.group(1)), s)
    s = re.sub(r"\b([a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,})\b", r'<a href="mailto:\1">\1</a>', s)
    return s


def convert(md):
    out, i, lines = [], 0, md.splitlines()
    title = ""
    while i < len(lines):
        line = lines[i]
        if line.startswith("<!--"):
            while "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            out.append("<h1>%s</h1>" % inline(title))
        elif line.startswith("## "):
            out.append("<h2>%s</h2>" % inline(line[3:].strip()))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-+", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append("<table>")
            for r, cells in enumerate(rows):
                tag = "th" if r == 0 else "td"
                out.append("<tr>" + "".join("<%s>%s</%s>" % (tag, inline(c), tag) for c in cells) + "</tr>")
            out.append("</table>")
            continue
        elif line.startswith("- "):
            out.append("<ul>")
            while i < len(lines) and (lines[i].startswith("- ") or (lines[i].startswith("  ") and lines[i].strip())):
                if lines[i].startswith("- "):
                    out.append("<li>%s" % inline(lines[i][2:].strip()))
                else:
                    out[-1] += " " + inline(lines[i].strip())
                i += 1
            out.append("</ul>")
            continue
        elif line.strip():
            para = [line.strip()]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||- |<!--)", lines[i + 1]):
                i += 1
                para.append(lines[i].strip())
            text = " ".join(para)
            cls = ' class="updated"' if text.startswith(DATED) else ""
            out.append("<p%s>%s</p>" % (cls, inline(text)))
        i += 1
    return title, "\n".join(out)


def read(lang):
    with io.open(os.path.join(LEGAL, "privacy-policy.%s.md" % lang), encoding="utf-8") as f:
        return convert(f.read())


def site():
    """The public page: English, then Turkish, in one file."""
    en_title, en = read("en")
    _, tr = read("tr")
    page = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
            "<section id=\"en\" lang=\"en\">\n<nav class=\"lang\"><a href=\"#tr\" hreflang=\"tr\">Türkçe</a></nav>\n%s\n</section>\n"
            "<section id=\"tr\" lang=\"tr\">\n<nav class=\"lang\"><a href=\"#en\" hreflang=\"en\">English</a></nav>\n%s\n</section>\n"
            "</body>\n</html>\n") % (html.escape(en_title), SITE_CSS, en, tr)
    os.makedirs(os.path.dirname(SITE), exist_ok=True)
    with io.open(SITE, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("wrote", os.path.relpath(SITE, os.path.join(HERE, "..", "..")), len(page), "bytes")


def main():
    for lang in ("tr", "en"):
        title, body = read(lang)
        page = ("<!DOCTYPE html>\n<html lang=\"%s\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n") % (lang, html.escape(title), CSS, body)
        dst = os.path.join(LEGAL, "privacy-policy.%s.html" % lang)
        with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print("wrote", os.path.relpath(dst, os.path.join(HERE, "..", "..")), len(page), "bytes")
        os.makedirs(GAME, exist_ok=True)
        with io.open(os.path.join(LEGAL, "privacy-policy.%s.md" % lang), encoding="utf-8") as f:
            md = f.read()
        with io.open(os.path.join(GAME, "privacy-policy.%s.md" % lang), "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
    if "--site" in sys.argv:
        site()


if __name__ == "__main__":
    main()
