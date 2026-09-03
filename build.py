#!/usr/bin/env python3
"""
Banksoft site build.

  python3 build.py

Produces:
  ./<page>.html, ./tr/<page>.html   static pages (EN at root, TR under /tr/)
  ./sitemap.xml, ./robots.txt
  ./dist/banksoft-preview.html      single-file preview (inlined CSS/JS, shared
                                    data-URI image store, hash routing, both
                                    languages) for sharing as an Artifact.
"""
import base64
import mimetypes
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SITE = "https://www.banksoft.com.tr"
PAGES = ["index", "solutions", "company", "news", "careers", "contact", "legal"]
LANGS = {
    "en": {"dir": "", "asset": "", "header": "header.html", "footer": "footer.html", "html_lang": "en"},
    "tr": {"dir": "tr/", "asset": "../", "header": "header.tr.html", "footer": "footer.tr.html", "html_lang": "tr"},
}

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@500;600;700&family=Source+Sans+3:wght@400;600&display=swap">'
)

css = (ROOT / "assets" / "css" / "style.css").read_text()
js = (ROOT / "assets" / "js" / "main.js").read_text()


def meta(html, key):
    m = re.search(r"<!--\s*%s:\s*(.*?)\s*-->" % key, html)
    return m.group(1) if m else ""


def strip_meta(html):
    return re.sub(r"<!--\s*(title|description):.*?-->\n?", "", html)


def mark_current(hdr, page):
    return re.sub(
        r'<a href="([a-z]+)\.html" data-page="%s"' % page,
        r'<a href="\1.html" data-page="%s" aria-current="page"' % page,
        hdr,
    )


def page_src(lang, page):
    sub = "tr/" if lang == "tr" else ""
    return (SRC / "pages" / sub / f"{page}.html").read_text()


def url_for(lang, page):
    fname = "" if page == "index" else f"{page}.html"
    return f"{SITE}/{LANGS[lang]['dir']}{fname}"


# ---------------------------------------------------------------- static pages
for lang, cfg in LANGS.items():
    header = (SRC / "partials" / cfg["header"]).read_text()
    footer = (SRC / "partials" / cfg["footer"]).read_text()
    outdir = ROOT / cfg["dir"] if cfg["dir"] else ROOT
    outdir.mkdir(exist_ok=True)
    for page in PAGES:
        src = page_src(lang, page)
        title, desc = meta(src, "title"), meta(src, "description")
        body = strip_meta(src)
        hdr = mark_current(header, page).replace("{{ALT}}", f"{page}.html")
        a = cfg["asset"]
        og_img = f"{SITE}/assets/img/building.jpg"
        alternates = "".join(
            f'<link rel="alternate" hreflang="{l}" href="{url_for(l, page)}">' for l in LANGS
        ) + f'<link rel="alternate" hreflang="x-default" href="{url_for("en", page)}">'
        doc = f"""<!doctype html>
<html lang="{cfg['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url_for(lang, page)}">
{alternates}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Banksoft">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url_for(lang, page)}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="{'tr_TR' if lang == 'tr' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#101B27">
<link rel="icon" href="{a}assets/img/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="{a}assets/css/style.css">
</head>
<body>
{hdr}
{body}
{footer}
<script src="{a}assets/js/main.js" defer></script>
</body>
</html>
"""
        (outdir / f"{page}.html").write_text(doc)
    print("wrote", lang, "pages")

# ---------------------------------------------------------------- sitemap/robots
today = date.today().isoformat()
urls = []
for page in PAGES:
    for lang in LANGS:
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url_for(l, page)}"/>' for l in LANGS
        )
        urls.append(f"  <url>\n    <loc>{url_for(lang, page)}</loc>\n    <lastmod>{today}</lastmod>{alts}\n  </url>")
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "\n".join(urls) + "\n</urlset>\n"
)
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
print("wrote sitemap.xml, robots.txt")

# ---------------------------------------------------------------- single file
def data_uri(path):
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


images = {}  # name -> data uri, embedded once


def share_images(html):
    def rep(m):
        name = m.group(2)
        p = ROOT / "assets" / "img" / name
        if p.exists():
            images.setdefault(name, data_uri(p))
            return f'data-img="{name}"'
        return m.group(0)
    return re.sub(r'src="(\.\./)?assets/img/([^"]+)"', rep, html)


def route_links(html, lang, page):
    pre = "tr-" if lang == "tr" else ""
    # cross-language links first
    if lang == "en":
        html = re.sub(r'href="tr/([a-z]+)\.html"', r'href="#tr-\1"', html)
    else:
        html = re.sub(r'href="\.\./([a-z]+)\.html"', r'href="#\1"', html)
    # page.html#anchor -> #[tr-]page/anchor ; page.html -> #[tr-]page
    html = re.sub(r'href="([a-z]+)\.html#([\w-]+)"', lambda m: f'href="#{pre}{m.group(1)}/{m.group(2)}"', html)
    html = re.sub(r'href="([a-z]+)\.html"', lambda m: f'href="#{pre}{m.group(1)}"', html)
    # in-page #anchor -> #[tr-]page/anchor
    html = re.sub(r'href="#([\w-]+)"(?![\w/])',
                  lambda m: m.group(0) if re.match(r'^(tr-)?[a-z]+$', m.group(1)) and m.group(1).replace("tr-", "") in PAGES
                  else f'href="#{pre}{page}/{m.group(1)}"', html)
    return html


def strip_embeds(html):
    html = re.sub(r'<iframe class="map__embed".*?</iframe>\s*', "", html, flags=re.S)
    return html.replace('class="map map--embed"', 'class="map"')


lang_blocks = []
for lang, cfg in LANGS.items():
    header = (SRC / "partials" / cfg["header"]).read_text()
    footer = (SRC / "partials" / cfg["footer"]).read_text()
    header = re.sub(r'href="(tr/|\.\./)\{\{ALT\}\}"', 'href="#" data-lang-toggle', header)
    header = route_links(share_images(header), lang, "index")
    footer = route_links(share_images(footer), lang, "index")
    sections = []
    for page in PAGES:
        src = strip_meta(page_src(lang, page))
        src = route_links(share_images(strip_embeds(src)), lang, page)
        pid = ("tr-" if lang == "tr" else "") + page
        sections.append(f'<div class="page" data-page="{pid}" hidden>\n{src}\n</div>')
    lang_blocks.append(f'<div class="site" data-lang="{lang}" lang="{cfg["html_lang"]}" hidden>\n{header}\n{"".join(sections)}\n{footer}\n</div>')

img_store = "{" + ",".join(f'"{k}":"{v}"' for k, v in images.items()) + "}"
page_ids = [p for p in PAGES] + [f"tr-{p}" for p in PAGES]

router = """
<script>
(function(){
  var IMGS = %s;
  var pages = %s;
  document.querySelectorAll("img[data-img]").forEach(function(im){ var d = IMGS[im.getAttribute("data-img")]; if (d) im.src = d; });
  function show(){
    var h = location.hash.replace(/^#/, "");
    var parts = h.split("/");
    var page = pages.indexOf(parts[0]) > -1 ? parts[0] : "index";
    var anchor = parts[1];
    var lang = page.indexOf("tr-") === 0 ? "tr" : "en";
    var bare = page.replace(/^tr-/, "");
    document.querySelectorAll(".site").forEach(function(s){ s.hidden = s.getAttribute("data-lang") !== lang; });
    document.querySelectorAll(".page").forEach(function(p){ p.hidden = p.getAttribute("data-page") !== page; });
    document.querySelectorAll("a[data-page]").forEach(function(a){
      if (a.getAttribute("data-page") === bare) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current");
    });
    document.querySelectorAll("[data-lang-toggle]").forEach(function(a){ a.setAttribute("href", lang === "en" ? "#tr-" + bare : "#" + bare); });
    document.querySelectorAll(".mobile-nav").forEach(function(m){ m.classList.remove("is-open"); });
    document.documentElement.lang = lang;
    if (anchor) { var el = document.querySelector('.site[data-lang="' + lang + '"] #' + anchor); if (el) { requestAnimationFrame(function(){ el.scrollIntoView({block:"start"}); }); return; } }
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", show);
  show();
})();
</script>
""" % (img_store, page_ids)

# main.js queries single elements (.menu-btn, .form); make it bind to every instance in the preview
js_all = js
for sel in [".menu-btn", ".mobile-nav", ".form"]:
    pass  # handled below by a small shim
shim = """
<script>
// Preview shim: main.js binds one header/form; here each language block has its own.
document.querySelectorAll(".site").forEach(function(site){
  var btn = site.querySelector(".menu-btn"), mob = site.querySelector(".mobile-nav");
  if (btn && mob && !btn.__bound) { btn.__bound = true; btn.addEventListener("click", function(){ var o = mob.classList.toggle("is-open"); btn.setAttribute("aria-expanded", o ? "true" : "false"); }); }
  var form = site.querySelector(".form");
  if (form && !form.__bound) { form.__bound = true; form.addEventListener("submit", function(ev){ ev.preventDefault(); var st = form.querySelector(".form__status"); st.className = "form__status is-ok"; st.textContent = form.getAttribute("data-msg-ok"); form.reset(); }); }
});
</script>
"""

preview = f"""<meta charset="utf-8">
<title>Banksoft</title>
{FONTS}
<style>
{css}
.site[hidden], .page[hidden] {{ display: none !important; }}
</style>
{"".join(lang_blocks)}
{router}
<script>
{js.replace('document.querySelector(".menu-btn")', 'null').replace('document.querySelector(".form")', 'null')}
</script>
{shim}
"""
dist = ROOT / "dist"
dist.mkdir(exist_ok=True)
out = dist / "banksoft-preview.html"
out.write_text(preview)
print("wrote", out.relative_to(ROOT), f"({out.stat().st_size/1024/1024:.1f} MB), images embedded once:", len(images))
