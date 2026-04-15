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
            f'<rect width="{width}" height="{height}" rx="24" fill="#f8fafc" />',
            '<text x="36" y="34" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700" fill="#0f172a">Flujo principal entre taskbots</text>',
            '<text x="36" y="56" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#475569">Las flechas muestran la direccion de la invocacion o dependencia entre bots.</text>',
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
            f'<path d="{path}" fill="none" stroke="#2563eb" stroke-width="3" marker-end="url(#arrow)" />'
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
                f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{text_width:.1f}" height="24" rx="12" fill="#dbeafe" stroke="#93c5fd" />'
            )
            elements.append(
                f'<text x="{label_x:.1f}" y="{label_y + 2:.1f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="600" fill="#1d4ed8">{safe_label}</text>'
            )
    return elements


def _build_svg_nodes(nodes, positions):
    elements = []
    for node in nodes:
        position = positions[node["id"]]
        x = position["x"]
        y = position["y"]
        accent = "#f97316" if node.get("is_entrypoint") else "#2563eb"
        fill = "#fff7ed" if node.get("is_entrypoint") else "#ffffff"
        role = str(node.get("role", "taskbot")).upper()
        detail = f"Nodos AA360: {node.get('node_count', 0)}"

        elements.append(
            f'<rect x="{x}" y="{y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="18" fill="{fill}" stroke="{accent}" stroke-width="3" />'
        )
        badge_fill = _blend_color(accent, 0.12, fill)
        elements.append(
            f'<rect x="{x + 16}" y="{y + 14}" width="86" height="24" rx="12" fill="{badge_fill}" />'
        )
        elements.append(
            f'<text x="{x + 59}" y="{y + 30}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="700" fill="{accent}">{html.escape(role)}</text>'
        )

        title_lines = _wrap_text(node["name"], 24, 2)
        title_y = y + 54
        for offset, line in enumerate(title_lines):
            elements.append(
                f'<text x="{x + 18}" y="{title_y + offset * 18}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="#0f172a">{html.escape(line)}</text>'
            )

        detail_y = y + 88
        elements.append(
            f'<text x="{x + 18}" y="{detail_y}" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#475569">{html.escape(detail)}</text>'
        )
        if node.get("is_entrypoint"):
            elements.append(
                f'<text x="{x + BOX_WIDTH - 18}" y="{detail_y}" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="600" fill="#9a3412">Inicio</text>'
            )

    return elements


def _build_svg_starts(nodes, positions):
    elements = []
    entrypoints = [node for node in nodes if node.get("is_entrypoint")]
    for index, node in enumerate(entrypoints, start=1):
        position = positions[node["id"]]
        cx = position["x"] - 70
        cy = position["y"] + BOX_HEIGHT / 2
        circle_fill = _blend_color("#0f172a", 0.9, "#f8fafc")
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="{START_RADIUS}" fill="{circle_fill}" />'
        )
        elements.append(
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="700" fill="#ffffff">IN</text>'
        )
        path = f"M {cx + START_RADIUS} {cy} L {position['x']} {cy}"
        elements.append(
            f'<path d="{path}" fill="none" stroke="#0f172a" stroke-width="2.5" marker-end="url(#arrowDark)" />'
        )
    return elements


def _svg_defs():
    return """
<defs>
  <marker id="arrow" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L14,7 L0,14 z" fill="#2563eb" />
  </marker>
  <marker id="arrowDark" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L14,7 L0,14 z" fill="#0f172a" />
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
            '<rect width="720" height="180" rx="24" fill="#f8fafc" />',
            '<text x="40" y="60" font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">Flujo principal entre taskbots</text>',
            f'<text x="40" y="110" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#475569">{safe_message}</text>',
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
