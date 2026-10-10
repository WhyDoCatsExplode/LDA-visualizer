#!/usr/bin/env python3
"""Pack src/template.html into the bundled index.html.

The HTML is a self-unpacking bundle: fonts, React and the design-system
runtime live base64-encoded in the __bundler/manifest block, and the page
itself is a JSON string in the __bundler/template block. Edit
src/template.html, then run `python3 build.py`.

The build also keeps a small capture script in the bundle's <head>. It runs
before the bundle unpacks and saves the page's own source (so "Export ›
Interactive page" can write a self-contained copy) plus any embedded
snapshot data (the corpus and model baked into an exported page).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
BUNDLE = ROOT / "index.html"
TEMPLATE = ROOT / "src" / "template.html"
TITLE = "LDA visualizer"
SITE_URL = "https://lda-visualizer.mikaeel.ca/"
DESCRIPTION = ("Interactive LDA topic model visualizer that runs entirely in the browser: "
               "upload text files or import models from R and Python.")

# Favicon ("LDA" in Geist on the site's #171717) and the unpack screen live here too.
# Social preview tags. They must live in this static shell: link-preview
# crawlers don't run the JavaScript that unpacks the page. og-image.png is the
# mikaeel.ca ribbon (RibbonWaveBackground at 655 CSS px wide, 2x, centre crop,
# toned to the main share image) with the site's IntertopicMap visual on top.
META = f"""<!-- lda-meta -->
  <meta name="description" content="{DESCRIPTION}">
  <meta property="og:title" content="{TITLE}">
  <meta property="og:description" content="{DESCRIPTION}">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:site_name" content="Mika">
  <meta property="og:type" content="website">
  <meta property="og:image" content="{SITE_URL}og-image.png">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="An intertopic distance map of coloured topic bubbles over the mikaeel.ca ribbon background">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{TITLE}">
  <meta name="twitter:description" content="{DESCRIPTION}">
  <meta name="twitter:image" content="{SITE_URL}og-image.png">
  <meta name="twitter:image:alt" content="An intertopic distance map of coloured topic bubbles over the mikaeel.ca ribbon background">
  <link rel="icon" href="favicon.png" type="image/png" sizes="32x32">
  <style id="lda-shell">
    /* Plain, theme-coloured screen while the bundle unpacks (no placeholder art or label). */
    #__bundler_loading {{ display: none !important; }}
    html.lda-light body, html.lda-light #__bundler_thumbnail {{ background: #fbfbfa; }}
  </style>
  <script>
    (function () {{
      var m = 'auto';
      try {{ m = localStorage.getItem('lda-theme') || 'auto'; }} catch (e) {{}}
      var dark = m === 'dark' || (m === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
      if (!dark) document.documentElement.classList.add('lda-light');
    }})();
  </script>
  <!-- /lda-meta -->"""

CAPTURE = """<script id="lda-capture">
    // Runs before the bundle unpacks (its DOMContentLoaded listener is registered first).
    document.addEventListener('DOMContentLoaded', function () {
      window.__ldaBundleSource = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
      var s = document.querySelector('script[type="application/x-lda-snapshot"]');
      if (s) try { window.__ldaSnapshot = JSON.parse(s.textContent); } catch (e) { console.error('snapshot', e); }
    });
  </script>"""

html = BUNDLE.read_text(encoding="utf-8")
tpl = TEMPLATE.read_text(encoding="utf-8")
# Same escaping the bundler uses: keep "</" from closing the <script> island.
encoded = json.dumps(tpl, ensure_ascii=False).replace("</", "<\\u002F")

pattern = re.compile(r'(<script type="__bundler/template">\n)(.*?)(\n  </script>)', re.S)
if not pattern.search(html):
    raise SystemExit("template block not found in bundle")
html = pattern.sub(lambda m: m.group(1) + encoded + m.group(3), html, count=1)

# Capture script: replace if present, else insert right after the shell's <title>.
html = re.sub(r'<title>.*?</title>', f'<title>{TITLE}</title>', html, count=1)
if 'id="lda-capture"' in html:
    html = re.sub(r'<script id="lda-capture">.*?</script>', lambda m: CAPTURE, html, count=1, flags=re.S)
else:
    html = html.replace(f'<title>{TITLE}</title>', f'<title>{TITLE}</title>\n  {CAPTURE}', 1)

# The bundler's placeholder art (four coloured circles) flashes on every load; keep the div, drop the art.
html = re.sub(r'(<div id="__bundler_thumbnail">).*?(</div>)', r"\1\2", html, count=1, flags=re.S)

# Social tags, favicon and unpack screen: replace if present, else insert right after <title>.
if "<!-- lda-meta -->" in html:
    html = re.sub(r"<!-- lda-meta -->.*?<!-- /lda-meta -->", lambda m: META, html, count=1, flags=re.S)
else:
    html = html.replace(f"<title>{TITLE}</title>", f"<title>{TITLE}</title>\n  {META}", 1)

BUNDLE.write_text(html, encoding="utf-8")
print(f"wrote {BUNDLE.name} ({len(html):,} bytes)")
