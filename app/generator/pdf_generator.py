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
    line-height: 1.5;
    color: #1a1a2e;
}
h1 {
    color: #0f3460;
    font-size: 20pt;
    border-bottom: 3px solid #e94560;
    padding-bottom: 8px;
    margin-top: 28px;
    margin-bottom: 14px;
}
h1:first-of-type {
    text-align: center;
    font-size: 26pt;
    border-bottom: 4px solid #e94560;
    padding-bottom: 12px;
    margin-top: 40px;
    margin-bottom: 6px;
}
h2 {
    color: #16213e;
    font-size: 15pt;
    border-bottom: 2px solid #0f3460;
    padding-bottom: 5px;
    margin-top: 22px;
    margin-bottom: 10px;
}
h3 {
    color: #0f3460;
    font-size: 12pt;
    margin-top: 16px;
    margin-bottom: 8px;
    border-left: 4px solid #e94560;
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
    color: #16213e;
}
code {
    font-family: Courier, monospace;
    font-size: 8.5pt;
    background-color: #f0f0f5;
    padding: 1px 4px;
    border-radius: 3px;
}
pre {
    background-color: #f4f4f8;
    border: 1px solid #d0d0d8;
    border-radius: 5px;
    padding: 12px;
    font-family: Courier, monospace;
    font-size: 7.5pt;
    line-height: 1.3;
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
    background-color: #0f3460;
    color: #ffffff;
}
th {
    padding: 7px 8px;
    text-align: left;
    font-weight: bold;
    border: 1px solid #0a2640;
}
td {
    padding: 5px 8px;
    border: 1px solid #c8c8d4;
    word-wrap: break-word;
}
tr:nth-child(even) {
    background-color: #f2f4f8;
}
tr:nth-child(odd) {
    background-color: #ffffff;
}
hr {
    border: none;
    border-top: 2px solid #e94560;
    margin: 20px 0;
}
blockquote {
    border-left: 4px solid #e94560;
    margin: 10px 0;
    padding: 8px 14px;
    background-color: #fdf2f4;
    font-style: italic;
    color: #444;
}
em {
    color: #555;
}
.cover-subtitle {
    text-align: center;
    font-size: 11pt;
    color: #555;
    margin-top: 4px;
    margin-bottom: 30px;
}
.badge {
    display: inline-block;
    background-color: #e94560;
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 8pt;
    font-weight: bold;
}
.footer-text {
    font-size: 7.5pt;
    color: #888;
    text-align: center;
    border-top: 1px solid #ddd;
    padding-top: 4px;
}
"""


def generate_sdd_pdf(md_content, output_path, project_name="Proyecto", flow_image_path=None):
    """Genera un PDF estilizado a partir del contenido Markdown del SDD."""
    try:
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc", "sane_lists"],
        )

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
    <p class="cover-subtitle">Documento de Diseno de Software — Generado automaticamente el {generated_date}</p>
    {html_body}
    <div id="page-footer">
        <p class="footer-text">SDD — {_escape_html(project_name)} | RPA-Doc-Generator | Pagina <pdf:pagenumber/></p>
    </div>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file, encoding="utf-8")

        if pisa_status.err:
            logger.error("Errores generando PDF SDD: %s", pisa_status.err)

        logger.info("SDD PDF guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error generando SDD PDF: %s", exc)
        raise


def generate_quality_pdf(md_content, output_path, project_name="Proyecto"):
    """Genera un PDF estilizado a partir del contenido Markdown del reporte de calidad."""
    try:
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
    <p class="cover-subtitle">Reporte de Calidad — Generado automaticamente el {generated_date}</p>
    {html_body}
    <div id="page-footer">
        <p class="footer-text">Calidad — {_escape_html(project_name)} | RPA-Doc-Generator | Pagina <pdf:pagenumber/></p>
    </div>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file, encoding="utf-8")

        if pisa_status.err:
            logger.error("Errores generando PDF calidad: %s", pisa_status.err)

        logger.info("Calidad PDF guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error generando Calidad PDF: %s", exc)
        raise


def _escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
