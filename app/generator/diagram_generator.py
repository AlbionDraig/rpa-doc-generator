import html
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

BOX_WIDTH = 270
BOX_HEIGHT = 108
COLUMN_GAP = 170
ROW_GAP = 48
MARGIN_X = 60
MARGIN_Y = 50
START_RADIUS = 18


def _blend_color(hex_color, opacity, bg="#ffffff"):
    """Pre-computes a solid color equivalent to hex_color at given opacity over bg."""
    c = hex_color.lstrip("#")
    b = bg.lstrip("#")
    cr, cg, cb = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    br, bg_val, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    r = round(cr * opacity + br * (1 - opacity))
    g = round(cg * opacity + bg_val * (1 - opacity))
    bl = round(cb * opacity + bb * (1 - opacity))
    return f"#{r:02x}{g:02x}{bl:02x}"

def generate_flow_svg(flow):
    """
    Genera un SVG autocontenido para visualizar la interaccion entre taskbots.
    """
    nodes = flow.get("nodes", [])
    if not nodes:
        return _empty_svg("No hay taskbots detectados")

    edges = flow.get("edges", [])
    positions, canvas = _calculate_layout(nodes, edges)
    defs = _svg_defs()
    edge_elements = _build_svg_edges(edges, positions)
    node_elements = _build_svg_nodes(nodes, positions)
    start_elements = _build_svg_starts(nodes, positions)

    width = canvas["width"]
    height = canvas["height"]
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Flujo principal entre taskbots">',
            defs,
            f'<rect width="{width}" height="{height}" rx="16" fill="#f8fafc" />',
            f'<rect x="0" y="0" width="{width}" height="64" rx="16" fill="#1e293b" />',
            f'<rect x="0" y="16" width="{width}" height="48" fill="#1e293b" />',
            '<text x="36" y="32" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="#f8fafc" letter-spacing="0.5">Flujo principal entre taskbots</text>',
            '<text x="36" y="50" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#94a3b8">Las flechas muestran la direccion de la invocacion o dependencia entre bots.</text>',
            *start_elements,
            *edge_elements,
            *node_elements,
            "</svg>",
        ]
    )


def _calculate_layout(nodes, edges):
    node_by_id = {node["id"]: node for node in nodes}
    incoming = {node["id"]: 0 for node in nodes}
    adjacency = defaultdict(list)
    reverse = defaultdict(list)

    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        reverse[edge["to"]].append(edge["from"])
        incoming[edge["to"]] += 1

    entry_ids = [node["id"] for node in nodes if node.get("is_entrypoint")] or [nodes[0]["id"]]
    levels = {node_id: 0 for node_id in entry_ids}
    queue = deque(entry_ids)

    while queue:
        current = queue.popleft()
        current_level = levels[current]
        for target in adjacency[current]:
            next_level = current_level + 1
            if next_level > levels.get(target, -1):
                levels[target] = next_level
                queue.append(target)

    for node in nodes:
        levels.setdefault(node["id"], 0 if incoming[node["id"]] == 0 else 1)

    layers = defaultdict(list)
    for node in nodes:
        layers[levels[node["id"]]].append(node)

    for layer_nodes in layers.values():
        layer_nodes.sort(key=lambda item: (0 if item.get("is_entrypoint") else 1, item["name"].lower()))

    positions = {}
    max_layer_size = max(len(layer_nodes) for layer_nodes in layers.values())
    max_level = max(layers.keys())
    diagram_top = 90
    content_height = max_layer_size * BOX_HEIGHT + max(0, max_layer_size - 1) * ROW_GAP
    canvas_height = diagram_top + content_height + MARGIN_Y
    canvas_width = MARGIN_X * 2 + (max_level + 1) * BOX_WIDTH + max_level * COLUMN_GAP + 100

    for level, layer_nodes in layers.items():
        layer_height = len(layer_nodes) * BOX_HEIGHT + max(0, len(layer_nodes) - 1) * ROW_GAP
        start_y = diagram_top + max((content_height - layer_height) / 2, 0)
        x = MARGIN_X + level * (BOX_WIDTH + COLUMN_GAP)

        for index, node in enumerate(layer_nodes):
            y = start_y + index * (BOX_HEIGHT + ROW_GAP)
            positions[node["id"]] = {"x": x, "y": y}

    return positions, {"width": int(canvas_width), "height": int(canvas_height)}


def _build_svg_edges(edges, positions):
    elements = []
    for edge in edges:
        source = positions[edge["from"]]
        target = positions[edge["to"]]

        x1 = source["x"] + BOX_WIDTH
        y1 = source["y"] + BOX_HEIGHT / 2
        x2 = target["x"]
        y2 = target["y"] + BOX_HEIGHT / 2
        curve_offset = min(80, abs(x2 - x1) / 2)

        path = (
            f"M {x1} {y1} "
            f"C {x1 + curve_offset} {y1}, {x2 - curve_offset} {y2}, {x2} {y2}"
        )
        elements.append(
            f'<path d="{path}" fill="none" stroke="#475569" stroke-width="2" stroke-dasharray="6,3" marker-end="url(#arrow)" />'
        )

        label = _build_edge_label(edge)
        if label:
            label_x = (x1 + x2) / 2
            label_y = min(y1, y2) - 12 if abs(y2 - y1) < 18 else (y1 + y2) / 2 - 10
            safe_label = html.escape(label)
            text_width = max(88, len(label) * 6.6)
            rect_x = label_x - text_width / 2
            rect_y = label_y - 14
            elements.append(
                f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{text_width:.1f}" height="24" rx="12" fill="#e0e7ff" stroke="#a5b4fc" />'
            )
            elements.append(
                f'<text x="{label_x:.1f}" y="{label_y + 2:.1f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="600" fill="#3730a3">{safe_label}</text>'
            )
    return elements


def _build_svg_nodes(nodes, positions):
    elements = []
    for node in nodes:
        position = positions[node["id"]]
        x = position["x"]
        y = position["y"]
        is_entry = node.get("is_entrypoint")
        accent = "#059669" if is_entry else "#4f46e5"
        fill = "#f0fdf4" if is_entry else "#eef2ff"
        stroke = "#059669" if is_entry else "#4f46e5"
        role = str(node.get("role", "taskbot")).upper()
        detail = f"Nodos AA360: {node.get('node_count', 0)}"

        elements.append(
            f'<rect x="{x}" y="{y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
        badge_fill = _blend_color(accent, 0.15, fill)
        elements.append(
            f'<rect x="{x + 14}" y="{y + 12}" width="90" height="22" rx="11" fill="{badge_fill}" />'
        )
        elements.append(
            f'<text x="{x + 59}" y="{y + 27}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" fill="{accent}">{html.escape(role)}</text>'
        )

        title_lines = _wrap_text(node["name"], 24, 2)
        title_y = y + 52
        for offset, line in enumerate(title_lines):
            elements.append(
                f'<text x="{x + 18}" y="{title_y + offset * 18}" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700" fill="#1e293b">{html.escape(line)}</text>'
            )

        detail_y = y + 88
        elements.append(
            f'<text x="{x + 18}" y="{detail_y}" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#64748b">{html.escape(detail)}</text>'
        )
        if is_entry:
            elements.append(
                f'<text x="{x + BOX_WIDTH - 18}" y="{detail_y}" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="600" fill="#065f46">Inicio</text>'
            )

    return elements


def _build_svg_starts(nodes, positions):
    elements = []
    entrypoints = [node for node in nodes if node.get("is_entrypoint")]
    for index, node in enumerate(entrypoints, start=1):
        position = positions[node["id"]]
        cx = position["x"] - 70
        cy = position["y"] + BOX_HEIGHT / 2
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="{START_RADIUS}" fill="#1e293b" />'
        )
        elements.append(
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" fill="#f8fafc">IN</text>'
        )
        path = f"M {cx + START_RADIUS} {cy} L {position['x']} {cy}"
        elements.append(
            f'<path d="{path}" fill="none" stroke="#1e293b" stroke-width="2" marker-end="url(#arrowDark)" />'
        )
    return elements


def _svg_defs():
    return """
<defs>
  <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L12,6 L0,12 z" fill="#475569" />
  </marker>
  <marker id="arrowDark" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L12,6 L0,12 z" fill="#1e293b" />
  </marker>
</defs>
""".strip()


def _build_edge_label(edge):
    label = edge.get("label", "")
    inputs_count = int(edge.get("inputs_count", 0) or 0)
    outputs_count = int(edge.get("outputs_count", 0) or 0)
    if inputs_count or outputs_count:
        return f"{label} | {inputs_count} in / {outputs_count} out"
    return label


def _wrap_text(value, max_chars, max_lines):
    words = str(value).split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break

    if len(lines) < max_lines:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(words) > 1 and len(" ".join(lines).split()) < len(words):
        lines[-1] = lines[-1][: max(0, max_chars - 3)].rstrip() + "..."

    return lines


def _empty_svg(message):
    safe_message = html.escape(message)
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="180" viewBox="0 0 720 180" role="img" aria-label="Flujo principal entre taskbots">',
            '<rect width="720" height="180" rx="16" fill="#f8fafc" />',
            '<rect x="0" y="0" width="720" height="56" rx="16" fill="#1e293b" />',
            '<rect x="0" y="16" width="720" height="40" fill="#1e293b" />',
            '<text x="36" y="34" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="#f8fafc">Flujo principal entre taskbots</text>',
            f'<text x="36" y="100" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="#64748b">{safe_message}</text>',
            "</svg>",
        ]
    )


def _escape_label(value):
    return str(value).replace('"', "'").replace("\r", " ").replace("\n", " ").strip()


def convert_svg_to_png(svg_path, png_path, scale=3.0):
    """Convierte un archivo SVG a PNG usando svglib + reportlab."""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM

        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            logger.warning("No se pudo parsear el SVG: %s", svg_path)
            return None

        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)

        renderPM.drawToFile(drawing, str(png_path), fmt="PNG", dpi=150)
        logger.info("SVG convertido a PNG: %s", png_path)
        return str(png_path)
    except Exception as exc:
        logger.error("Error convirtiendo SVG a PNG: %s", exc)
        return None
