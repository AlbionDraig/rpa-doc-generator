import base64
import logging
import re
from datetime import datetime
from pathlib import Path

import markdown
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

CSS_STYLE = """
@page {
    size: A4;
    margin: 2cm 2.2cm 2.5cm 2.2cm;
    @frame footer {
        -pdf-frame-content: page-footer;
        bottom: 0.5cm;
        margin-left: 2.2cm;
        margin-right: 2.2cm;
        height: 1.2cm;
    }
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1e293b;
}
h1 {
    color: #1e293b;
    font-size: 18pt;
    border-bottom: 2px solid #4f46e5;
    padding-bottom: 6px;
    margin-top: 30px;
    margin-bottom: 12px;
    letter-spacing: 0.3px;
}
h1:first-of-type {
    text-align: center;
    font-size: 24pt;
    border-bottom: 3px solid #4f46e5;
    padding-bottom: 10px;
    margin-top: 36px;
    margin-bottom: 6px;
}
h2 {
    color: #334155;
    font-size: 14pt;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 10px;
}
h3 {
    color: #334155;
    font-size: 11.5pt;
    margin-top: 16px;
    margin-bottom: 8px;
    border-left: 3px solid #4f46e5;
    padding-left: 10px;
}
p {
    margin: 4px 0;
}
ul {
    margin: 6px 0 6px 18px;
}
li {
    margin-bottom: 3px;
}
strong {
    color: #1e293b;
}
code {
    font-family: Courier, monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #4f46e5;
}
pre {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #4f46e5;
    border-radius: 4px;
    padding: 12px 14px;
    font-family: Courier, monospace;
    font-size: 7.5pt;
    line-height: 1.4;
    overflow: hidden;
    white-space: pre-wrap;
    word-wrap: break-word;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 9pt;
}
thead tr {
    background-color: #1e293b;
    color: #ffffff;
}
th {
    padding: 7px 8px;
    text-align: left;
    font-weight: bold;
    border: 1px solid #1e293b;
}
td {
    padding: 5px 8px;
    border: 1px solid #e2e8f0;
    word-wrap: break-word;
}
tr:nth-child(even) {
    background-color: #f1f5f9;
}
tr:nth-child(odd) {
    background-color: #ffffff;
}
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 22px 0;
}
blockquote {
    border-left: 3px solid #4f46e5;
    margin: 10px 0;
    padding: 8px 14px;
    background-color: #eef2ff;
    font-style: italic;
    color: #334155;
}
em {
    color: #64748b;
}
.cover-subtitle {
    text-align: center;
    font-size: 10pt;
    color: #64748b;
    margin-top: 4px;
    margin-bottom: 28px;
    letter-spacing: 0.5px;
}
.badge {
    display: inline-block;
    background-color: #4f46e5;
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 8pt;
    font-weight: bold;
}
.footer-text {
    font-size: 7.5pt;
    color: #94a3b8;
    text-align: center;
    border-top: 1px solid #e2e8f0;
    padding-top: 4px;
}
"""


_EMOJI_MAP = {
    "📁": "[DIR]",
    "📝": "",
    "🤖": "",
    "📊": "",
    "📄": "",
}


def _sanitize_tree_for_pdf(text):
    """Replace emoji characters that xhtml2pdf cannot render."""
    for emoji, replacement in _EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    return text


def _fix_pre_newlines(html):
    """Replace newlines with <br/> inside <pre> blocks so xhtml2pdf renders them."""
    def _replace_newlines(match):
        content = match.group(1)
        content = content.replace("\n", "<br/>")
        return f"<pre><code>{content}</code></pre>"
    return re.sub(r"<pre><code>(.*?)</code></pre>", _replace_newlines, html, flags=re.DOTALL)


def _fix_heading_anchors(html):
    """Convert heading id attributes to <a name> anchors for xhtml2pdf internal links."""
    def _add_anchor(match):
        tag = match.group(1)
        hid = match.group(2)
        content = match.group(3)
        return f'<{tag}><a name="{hid}"></a>{content}</{tag}>'
    return re.sub(
        r'<(h[1-6])\s+id="([^"]+)">(.*?)</\1>',
        _add_anchor,
        html,
    )


def generate_sdd_pdf(md_content, output_path, project_name="Proyecto", flow_image_path=None):
    """Genera un PDF estilizado a partir del contenido Markdown del SDD."""
    try:
        md_content = _sanitize_tree_for_pdf(md_content)
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc", "sane_lists"],
        )
        html_body = _fix_pre_newlines(html_body)
        html_body = _fix_heading_anchors(html_body)

        # Replace the relative SVG img tag with a base64-encoded PNG
        if flow_image_path and Path(flow_image_path).exists():
            png_data = Path(flow_image_path).read_bytes()
            b64 = base64.b64encode(png_data).decode("ascii")
            data_uri = f"data:image/png;base64,{b64}"
            html_body = re.sub(
                r'<img[^>]*src="flujo_taskbots\.svg"[^>]*/?>',
                f'<img src="{data_uri}" width="520"/>',
                html_body,
            )
        else:
            html_body = re.sub(
                r'<img[^>]*src="flujo_taskbots\.svg"[^>]*/?>',
                "<p><em>No se genero una imagen del flujo.</em></p>",
                html_body,
            )

        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>{CSS_STYLE}</style>
</head>
<body>
    <p class="cover-subtitle">Documento de Diseno de Software &mdash; Generado el {generated_date}</p>
    {html_body}
    <div id="page-footer">
        <p class="footer-text">SDD &mdash; {_escape_html(project_name)} &nbsp;|&nbsp; RPA-Doc-Generator &nbsp;|&nbsp; Pagina <pdf:pagenumber/></p>
    </div>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file, encoding="utf-8")  # type: ignore[union-attr]

        if pisa_status.err:  # type: ignore[union-attr]
            logger.error("Errores generando PDF SDD: %s", pisa_status.err)  # type: ignore[union-attr]

        logger.info("SDD PDF guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error generando SDD PDF: %s", exc)
        raise


def generate_quality_pdf(md_content, output_path, project_name="Proyecto"):
    """Genera un PDF estilizado a partir del contenido Markdown del reporte de calidad."""
    try:
        md_content = _sanitize_tree_for_pdf(md_content)
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "sane_lists"],
        )

        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>{CSS_STYLE}</style>
</head>
<body>
    <p class="cover-subtitle">Reporte de Calidad &mdash; Generado el {generated_date}</p>
    {html_body}
    <div id="page-footer">
        <p class="footer-text">Calidad &mdash; {_escape_html(project_name)} &nbsp;|&nbsp; RPA-Doc-Generator &nbsp;|&nbsp; Pagina <pdf:pagenumber/></p>
    </div>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file, encoding="utf-8")  # type: ignore[union-attr]

        if pisa_status.err:  # type: ignore[union-attr]
            logger.error("Errores generando PDF calidad: %s", pisa_status.err)  # type: ignore[union-attr]

        logger.info("Calidad PDF guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error generando Calidad PDF: %s", exc)
        raise


def _escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
