"""
Preview shell HTML generator for Simple Markdown Editor.
Generates a static page loaded once per theme; content is updated via innerHTML.
"""

from pygments.formatters import HtmlFormatter


def _shell_html(theme: dict, dark: bool) -> str:
    """Static page loaded once per theme. Content is updated via innerHTML."""
    t = theme
    # Pygments CSS for syntax highlighting
    style_name = "github-dark" if dark else "github"
    try:
        pygments_css = HtmlFormatter(style=style_name).get_style_defs(".codehilite")
    except Exception:
        pygments_css = HtmlFormatter(style="default").get_style_defs(".codehilite")

    return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  body {{
    margin: 0; padding: 24px 32px;
    font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
    font-size: 15px; line-height: 1.75;
    background: {t['surface']}; color: {t['text']};
  }}
  h1,h2,h3,h4,h5,h6 {{ font-weight:700; margin:1.4em 0 .5em; color:{t['accent']}; }}
  h1 {{ font-size:1.9em; border-bottom:2px solid {t['accent']}; padding-bottom:.25em; }}
  h2 {{ font-size:1.45em; border-bottom:1px solid {t['border']}; padding-bottom:.2em; }}
  h3 {{ font-size:1.2em; }}
  p {{ margin:.75em 0; }}
  a {{ color:{t['accent']}; text-decoration:underline; }}
  strong {{ font-weight:700; }} em {{ font-style:italic; }}
  del {{ text-decoration:line-through; color:{t['text2']}; }}
  code {{
    font-family:'JetBrains Mono','Fira Code','Consolas',monospace;
    font-size:.88em; background:{t['surface2']}; padding:.15em .4em;
    border-radius:4px; color:{t['accent']};
  }}
  pre {{
    background:{t['surface2']}; border:1px solid {t['border']}; border-radius:6px;
    padding:0; overflow-x:auto; margin:1em 0;
  }}
  pre code {{ background:none; padding:0; color:{t['text']}; font-size:.85em; }}
  .codehilite {{ padding:16px; margin:0; }}
  .codehilite pre {{ padding:0; border:none; margin:0; background:transparent; }}
  blockquote {{
    border-left:3px solid {t['accent']}; margin:1em 0; padding:.5em 1em;
    color:{t['text2']}; background:{t['accent_bg']}; border-radius:0 6px 6px 0;
  }}
  ul, ol {{ padding-left:1.5em; margin:.75em 0; }}
  li {{ margin:.3em 0; }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; }}
  th, td {{ border:1px solid {t['border']}; padding:.5em .8em; text-align:left; }}
  th {{ background:{t['surface2']}; font-weight:600; }}
  tr:nth-child(even) td {{ background:{t['surface2']}; }}
  img {{ max-width:100%; border-radius:6px; }}
  hr {{ border:none; border-top:1px solid {t['border']}; margin:1.5em 0; }}
  /* mermaid diagrams */
  .mermaid {{
    position: relative; text-align: center; margin: 1em 0;
    padding: 16px 16px 44px;
    background: {t['surface2']}; border: 1px solid {t['border']}; border-radius: 6px;
    overflow-x: auto;
  }}
  .diagram-actions {{
    position: absolute; bottom: 8px; right: 8px;
    display: flex; gap: 6px;
    opacity: 0; transition: opacity .2s;
  }}
  .mermaid:hover .diagram-actions {{ opacity: 1; }}
  .diagram-btn {{
    padding: 3px 10px; font-size: 11px; cursor: pointer;
    border: 1px solid {t['border']}; border-radius: 4px;
    background: {t['surface']}; color: {t['text2']};
    font-family: 'JetBrains Mono', monospace;
    transition: background .15s, color .15s, border-color .15s;
  }}
  .diagram-btn:hover {{ background: {t['accent']}; color: #fff; border-color: {t['accent']}; }}
  .diagram-btn.ok {{ background: #2a7a2a; color: #fff; border-color: #2a7a2a; }}
  .diagram-btn.ng {{ background: #a02020; color: #fff; border-color: #a02020; }}
  ::-webkit-scrollbar {{ width:6px; height:6px; }}
  ::-webkit-scrollbar-track {{ background:{t['surface2']}; }}
  ::-webkit-scrollbar-thumb {{ background:{t['border']}; border-radius:3px; }}
  /* Pygments */
  {pygments_css}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  const _mermaidTheme = '{"dark" if dark else "default"}';
  const BASE_FONT_SIZE = 14;
  let _currentFontSize = BASE_FONT_SIZE;

  function _initMermaid() {{
    mermaid.initialize({{ startOnLoad: false, theme: _mermaidTheme }});
  }}
  _initMermaid();

  // Scale a rendered mermaid SVG by setting width/height from viewBox × scale factor.
  // This is more reliable than mermaid's fontSize config option.
  function scaleSvg(svg) {{
    const vb = svg.viewBox && svg.viewBox.baseVal;
    if (!vb || vb.width === 0) return;
    const scale = _currentFontSize / BASE_FONT_SIZE;
    svg.setAttribute('width',  (vb.width  * scale).toFixed(1));
    svg.setAttribute('height', (vb.height * scale).toFixed(1));
  }}

  // Called from Python on font size change — scales all existing diagrams instantly
  window.applyFontSize = function(px) {{
    _currentFontSize = px;
    document.body.style.fontSize = px + 'px';
    document.querySelectorAll('.mermaid svg').forEach(scaleSvg);
  }};

  // SVG → PNG data URL (2× retina, white background)
  // Uses viewBox for full diagram size, not the clipped viewport rect.
  function svgToPngDataUrl(svg) {{
    return new Promise((resolve, reject) => {{
      // Prefer viewBox (full diagram) over getBoundingClientRect (visible area only)
      const vb = svg.viewBox && svg.viewBox.baseVal;
      const w = (vb && vb.width  > 0) ? vb.width  : (svg.getBoundingClientRect().width  || 800);
      const h = (vb && vb.height > 0) ? vb.height : (svg.getBoundingClientRect().height || 400);

      // Clone and set explicit px dimensions so the browser renders at full size
      const clone = svg.cloneNode(true);
      clone.setAttribute('width',  w);
      clone.setAttribute('height', h);
      // Ensure xmlns is present for standalone serialization
      if (!clone.getAttribute('xmlns'))
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

      const svgData = new XMLSerializer().serializeToString(clone);
      const b64 = btoa(unescape(encodeURIComponent(svgData)));
      const img = new Image();
      img.onload = () => {{
        const scale = 2;
        const canvas = document.createElement('canvas');
        canvas.width  = w * scale;
        canvas.height = h * scale;
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0, w, h);
        resolve(canvas.toDataURL('image/png'));
      }};
      img.onerror = reject;
      img.src = 'data:image/svg+xml;base64,' + b64;
    }});
  }}

  async function copyAsPng(svg, btn) {{
    const orig = btn.textContent;
    try {{
      const dataUrl = await svgToPngDataUrl(svg);
      const res   = await fetch(dataUrl);
      const blob  = await res.blob();
      await navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]);
      btn.textContent = '✓ Copied!'; btn.classList.add('ok');
      setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('ok'); }}, 2000);
    }} catch(e) {{
      btn.textContent = '✗ Error'; btn.classList.add('ng');
      setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('ng'); }}, 2000);
      console.error('Copy PNG failed:', e);
    }}
  }}

  function downloadSvg(svg, idx) {{
    const svgData = new XMLSerializer().serializeToString(svg);
    const dataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);
    const a = document.createElement('a');
    a.href     = dataUrl;
    a.download = 'diagram_' + (idx + 1) + '.svg';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  }}

  function addDiagramActions(el, idx) {{
    if (el.dataset.actions) return;
    el.dataset.actions = '1';
    const svg = el.querySelector('svg');
    if (!svg) return;
    scaleSvg(svg);  // apply current font size scale immediately after render
    const wrap = document.createElement('div');
    wrap.className = 'diagram-actions';
    const pngBtn = document.createElement('button');
    pngBtn.className = 'diagram-btn';
    pngBtn.textContent = '📋 Copy PNG';
    pngBtn.onclick = () => copyAsPng(svg, pngBtn);
    const svgBtn = document.createElement('button');
    svgBtn.className = 'diagram-btn';
    svgBtn.textContent = '⬇ SVG';
    svgBtn.onclick = () => downloadSvg(svg, idx);
    wrap.appendChild(pngBtn); wrap.appendChild(svgBtn);
    el.appendChild(wrap);
  }}
</script>
</head>
<body><div id="content"></div></body>
</html>
"""
