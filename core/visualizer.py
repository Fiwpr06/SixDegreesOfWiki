"""Render bounded interactive PyVis graph, connected path stepper and global themes with custom SVG icons."""

from html import escape
import json

from pyvis.network import Network

from utils.exporter import article_url
from .search_types import SearchResult


# Custom vector icons representing specific functional roles
SVG_START = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>'
SVG_MID = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'
SVG_TARGET = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
SVG_ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>'
SVG_EXT = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
SVG_ROUTE = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M12 19h4.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H12"/></svg>'
SVG_INFO = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'


THEMES = {
    "cosmic": {
        "name": "Cosmic Deep Space (Tối vũ trụ)",
        "canvas_bg": "#0b0d17",
        "sidebar_bg": "#070912",
        "card_bg": "#151928",
        "input_bg": "#121524",
        "border": "#252e4d",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "primary": "#00d2e6",
        "start_node": "#00d2e6",
        "start_border": "#38bdf8",
        "start_text": "#38bdf8",
        "start_bg": "rgba(0, 210, 230, 0.12)",
        "target_node": "#f43f5e",
        "target_border": "#fb7185",
        "target_text": "#fb7185",
        "target_bg": "rgba(244, 63, 94, 0.12)",
        "mid_node": "#a855f7",
        "mid_border": "#c084fc",
        "mid_text": "#c084fc",
        "mid_bg": "rgba(168, 85, 247, 0.12)",
        "other_node": "#334155",
        "other_border": "#475569",
        "path_edge": "#00d2e6",
        "other_edge": "#1f2740",
        "arrow_color": "#38bdf8",
    },
    "nier": {
        "name": "NieR: Automata (Sáng hoài niệm / YoRHa)",
        "canvas_bg": "#e5e0d8",
        "sidebar_bg": "#ddd7cc",
        "card_bg": "#d8d1c2",
        "input_bg": "#f5f2eb",
        "border": "#b5ad9d",
        "text": "#24211d",
        "text_muted": "#5c5545",
        "primary": "#2e5252",
        "start_node": "#2e5252",
        "start_border": "#3d6b6b",
        "start_text": "#1e3838",
        "start_bg": "rgba(46, 82, 82, 0.12)",
        "target_node": "#9e3a24",
        "target_border": "#bf4e34",
        "target_text": "#591e12",
        "target_bg": "rgba(158, 58, 36, 0.12)",
        "mid_node": "#7a6c58",
        "mid_border": "#96866f",
        "mid_text": "#3f3629",
        "mid_bg": "rgba(122, 108, 88, 0.12)",
        "other_node": "#c4beaf",
        "other_border": "#b8b2a4",
        "path_edge": "#2e5252",
        "other_edge": "#c8c2b4",
        "arrow_color": "#574f3f",
    },
    "cyberpunk": {
        "name": "Cyberpunk Slate (Tối công nghệ)",
        "canvas_bg": "#0b0e14",
        "sidebar_bg": "#07090d",
        "card_bg": "#151c2c",
        "input_bg": "#111624",
        "border": "#2a354c",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "primary": "#38bdf8",
        "start_node": "#38bdf8",
        "start_border": "#7dd3fc",
        "start_text": "#7dd3fc",
        "start_bg": "rgba(56, 189, 248, 0.12)",
        "target_node": "#f59e0b",
        "target_border": "#fbbf24",
        "target_text": "#fbbf24",
        "target_bg": "rgba(245, 158, 11, 0.12)",
        "mid_node": "#10b981",
        "mid_border": "#34d399",
        "mid_text": "#34d399",
        "mid_bg": "rgba(16, 185, 129, 0.12)",
        "other_node": "#222d40",
        "other_border": "#334155",
        "path_edge": "#38bdf8",
        "other_edge": "#1e2638",
        "arrow_color": "#00d2e6",
    },
    "paper": {
        "name": "Clean Paper (Sáng tối giản)",
        "canvas_bg": "#f8fafc",
        "sidebar_bg": "#f1f5f9",
        "card_bg": "#ffffff",
        "input_bg": "#ffffff",
        "border": "#cbd5e1",
        "text": "#0f172a",
        "text_muted": "#475569",
        "primary": "#0284c7",
        "start_node": "#0284c7",
        "start_border": "#0ea5e9",
        "start_text": "#0369a1",
        "start_bg": "rgba(2, 132, 199, 0.08)",
        "target_node": "#d97706",
        "target_border": "#f59e0b",
        "target_text": "#b45309",
        "target_bg": "rgba(217, 119, 6, 0.08)",
        "mid_node": "#059669",
        "mid_border": "#10b981",
        "mid_text": "#047857",
        "mid_bg": "rgba(5, 150, 105, 0.08)",
        "other_node": "#cbd5e1",
        "other_border": "#94a3b8",
        "path_edge": "#0284c7",
        "other_edge": "#cbd5e1",
        "arrow_color": "#0284c7",
    },
}


def global_theme_css(theme_name: str = "cosmic") -> str:
    """Inject global CSS rules to theme the entire Streamlit page and controls."""
    theme = THEMES.get(theme_name, THEMES["cosmic"])
    return f"""
    <style>
    /* Global App Canvas & Background */
    .stApp, [data-testid="stAppViewContainer"], .main {{
        background-color: {theme['canvas_bg']} !important;
        color: {theme['text']} !important;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {theme['sidebar_bg']} !important;
        border-right: 1px solid {theme['border']} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {theme['text']} !important;
    }}
    section[data-testid="stSidebar"] .stCaption p {{
        color: {theme['text_muted']} !important;
    }}

    /* Header & Top Bar */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* Metric Cards */
    [data-testid="stMetric"] {{
        background-color: {theme['card_bg']} !important;
        border: 1px solid {theme['border']} !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    }}
    [data-testid="stMetricLabel"] p {{
        color: {theme['text_muted']} !important;
        font-size: 13px !important;
    }}
    [data-testid="stMetricValue"] div {{
        color: {theme['text']} !important;
        font-weight: 700 !important;
    }}

    /* Input Fields & Selectboxes */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text']} !important;
        border: 1px solid {theme['border']} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text']} !important;
        border-color: {theme['border']} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] * {{
        color: {theme['text']} !important;
    }}
    div[data-baseweb="popover"] ul {{
        background-color: {theme['card_bg']} !important;
        border: 1px solid {theme['border']} !important;
    }}
    div[data-baseweb="popover"] li {{
        color: {theme['text']} !important;
    }}

    /* Tabs */
    div[data-baseweb="tab-list"] {{
        border-bottom: 1px solid {theme['border']} !important;
        gap: 8px !important;
    }}
    button[data-baseweb="tab"] {{
        color: {theme['text_muted']} !important;
        font-weight: 500 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {theme['primary']} !important;
        border-bottom-color: {theme['primary']} !important;
        font-weight: 600 !important;
    }}

    /* Action Buttons */
    .stButton > button[kind="primary"] {{
        background-color: {theme['primary']} !important;
        border: 1px solid {theme['primary']} !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }}
    .stButton > button[kind="secondary"] {{
        background-color: {theme['card_bg']} !important;
        border: 1px solid {theme['border']} !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
    }}
    .stDownloadButton > button {{
        background-color: {theme['card_bg']} !important;
        border: 1px solid {theme['border']} !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
    }}

    /* Alerts / Info Boxes */
    div[data-testid="stAlert"] {{
        background-color: {theme['card_bg']} !important;
        border: 1px solid {theme['border']} !important;
        color: {theme['text']} !important;
    }}
    div[data-testid="stAlert"] p {{
        color: {theme['text']} !important;
    }}

    /* Code Blocks & Tables */
    div[data-testid="stCodeBlock"] pre {{
        background-color: {theme['input_bg']} !important;
        border: 1px solid {theme['border']} !important;
        color: {theme['text']} !important;
    }}
    div[data-testid="stDataFrame"] {{
        border: 1px solid {theme['border']} !important;
        border-radius: 8px !important;
    }}

    /* Headings and Captions */
    h1, h2, h3, h4, h5, h6 {{
        color: {theme['text']} !important;
    }}
    .stCaption, .stCaption p {{
        color: {theme['text_muted']} !important;
    }}
    </style>
    """


def path_stepper_html(result: SearchResult, theme_name: str = "cosmic") -> str:
    """Generate a sleek, connected step-by-step pipeline with self-drawn SVG icons."""
    theme = THEMES.get(theme_name, THEMES["cosmic"])
    path = result.path
    if not path:
        return ""

    steps_html = []
    total_steps = len(path)

    for step, title in enumerate(path):
        url = article_url(title, result.lang)
        escaped_title = escape(title)

        if step == 0:
            role_class = "wiki-step-start"
            badge_class = "wiki-badge-start"
            badge_text = "Khởi hành"
            icon = SVG_START
        elif step == total_steps - 1:
            role_class = "wiki-step-target"
            badge_class = "wiki-badge-target"
            badge_text = "Đích đến"
            icon = SVG_TARGET
        else:
            role_class = "wiki-step-mid"
            badge_class = "wiki-badge-mid"
            badge_text = f"Bước {step}"
            icon = SVG_MID

        step_node = f"""
        <a href="{url}" target="_blank" rel="noopener noreferrer"
           class="wiki-step-link {role_class}"
           title="Nhấp để mở bài '{escaped_title}' trên Wikipedia">
            <span class="wiki-badge {badge_class}">{icon} <span>{badge_text}</span></span>
            <span class="wiki-title">{escaped_title}</span>
            <span class="wiki-ext-icon">{SVG_EXT}</span>
        </a>
        """
        steps_html.append(step_node)

        if step < total_steps - 1:
            steps_html.append(f'<div class="wiki-arrow">{SVG_ARROW}</div>')

    flow_content = "".join(steps_html)

    return f"""
    <style>
    .wiki-stepper-container {{
        background: {theme["card_bg"]};
        border: 1px solid {theme["border"]};
        border-radius: 12px;
        padding: 16px 20px;
        margin: 14px 0 20px 0;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .wiki-stepper-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px dashed {theme["border"]};
        color: {theme["text_muted"]};
        font-size: 13px;
    }}
    .wiki-stepper-title {{
        display: flex;
        align-items: center;
        gap: 7px;
        color: {theme["text"]};
        font-weight: 600;
        font-size: 14px;
    }}
    .wiki-stepper-hint {{
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
        color: {theme["text_muted"]};
    }}
    .wiki-stepper-flow {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
    }}
    .wiki-step-link {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 13px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 13.5px;
        font-weight: 500;
        transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
        cursor: pointer;
    }}
    .wiki-step-link:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.18);
        filter: brightness(1.08);
    }}
    .wiki-step-start {{
        background: {theme["start_bg"]};
        border: 1.5px solid {theme["start_border"]};
        color: {theme["start_text"]};
    }}
    .wiki-step-mid {{
        background: {theme["mid_bg"]};
        border: 1.5px solid {theme["mid_border"]};
        color: {theme["mid_text"]};
    }}
    .wiki-step-target {{
        background: {theme["target_bg"]};
        border: 1.5px solid {theme["target_border"]};
        color: {theme["target_text"]};
    }}
    .wiki-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.3px;
    }}
    .wiki-badge-start {{
        background: {theme["start_node"]};
        color: #ffffff;
    }}
    .wiki-badge-mid {{
        background: {theme["mid_node"]};
        color: #ffffff;
    }}
    .wiki-badge-target {{
        background: {theme["target_node"]};
        color: #ffffff;
    }}
    .wiki-title {{
        word-break: break-word;
    }}
    .wiki-arrow {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: {theme["arrow_color"]};
        user-select: none;
    }}
    .wiki-ext-icon {{
        display: inline-flex;
        align-items: center;
        opacity: 0.7;
        margin-left: 2px;
    }}
    </style>
    <div class="wiki-stepper-container">
        <div class="wiki-stepper-header">
            <span class="wiki-stepper-title">
                {SVG_ROUTE}
                <span>Hành trình liên kết ({total_steps} bài viết · {result.depth} bước nhảy)</span>
            </span>
            <span class="wiki-stepper-hint">
                {SVG_INFO}
                <span>Nhấp vào bài viết hoặc nút đồ thị để mở Wikipedia</span>
            </span>
        </div>
        <div class="wiki-stepper-flow">
            {flow_content}
        </div>
    </div>
    """


def graph_html(result: SearchResult, theme_name: str = "cosmic") -> str:
    """Render an interactive PyVis graph with theme matching and node click-to-wiki."""
    theme = THEMES.get(theme_name, THEMES["cosmic"])

    graph = Network(
        height="540px",
        width="100%",
        directed=True,
        bgcolor=theme["canvas_bg"],
        font_color=theme["text"],
        cdn_resources="in_line"
    )

    path = result.path
    path_edges = set(zip(path, path[1:]))
    edges = set(result.edges) | path_edges
    nodes = set(path)
    for source, target in edges:
        nodes.add(source)
        nodes.add(target)

    # URL dictionary for client-side click event
    url_map = {node: article_url(node, result.lang) for node in nodes}

    for node in nodes:
        if node == result.start:
            color = {
                "background": theme["start_node"],
                "border": theme["start_border"],
                "highlight": {"background": theme["start_node"], "border": "#ffffff"},
            }
            size = 30
        elif node == result.target:
            color = {
                "background": theme["target_node"],
                "border": theme["target_border"],
                "highlight": {"background": theme["target_node"], "border": "#ffffff"},
            }
            size = 30
        elif node in path:
            color = {
                "background": theme["mid_node"],
                "border": theme["mid_border"],
                "highlight": {"background": theme["mid_node"], "border": "#ffffff"},
            }
            size = 24
        else:
            color = {
                "background": theme["other_node"],
                "border": theme["other_border"],
                "highlight": {"background": theme["other_node"], "border": "#ffffff"},
            }
            size = 14

        escaped = escape(node)
        tooltip = (
            f"<div style='font-family: sans-serif; padding: 4px;'>"
            f"<b>{escaped}</b><br>"
            f"<span style='color: {theme['primary']};'>Nhấp để mở bài trên Wikipedia</span>"
            f"</div>"
        )

        graph.add_node(
            node,
            label=node,
            title=tooltip,
            color=color,
            size=size,
            font={"color": theme["text"], "size": 13, "face": "sans-serif"},
            borderWidth=2,
        )

    for source, target in edges:
        highlight = (source, target) in path_edges
        graph.add_edge(
            source,
            target,
            color=theme["path_edge"] if highlight else theme["other_edge"],
            width=3.5 if highlight else 1,
            arrows="to",
            smooth={"type": "cubicBezier", "roundness": 0.15} if highlight else {"type": "continuous"},
        )

    # Set stable, compact physics options
    options = {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -2800,
                "centralGravity": 0.35,
                "springLength": 130,
                "springConstant": 0.04,
                "damping": 0.1,
                "avoidOverlap": 0.2,
            },
            "stabilization": {"iterations": 250, "updateInterval": 25},
        },
        "interaction": {
            "hover": True,
            "zoomView": True,
            "dragView": True,
            "dragNodes": True,
            "tooltipDelay": 80,
        },
    }
    graph.set_options(json.dumps(options))

    html = graph.generate_html(notebook=False)

    # Inject click-to-wiki JavaScript
    url_json = json.dumps(url_map, ensure_ascii=False)
    injection = f"""
    network = new vis.Network(container, data, options);
    var articleUrls = {url_json};
    network.on("click", function(params) {{
        if (params.nodes && params.nodes.length > 0) {{
            var clickedNode = params.nodes[0];
            var targetUrl = articleUrls[clickedNode];
            if (targetUrl) {{
                window.open(targetUrl, "_blank");
            }}
        }}
    }});
    """

    html = html.replace("network = new vis.Network(container, data, options);", injection, 1)

    # Replace container styling with theme-based borders
    old_border = "border: 1px solid lightgray;"
    new_border = f"border: 1px solid {theme['border']}; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.18);"
    html = html.replace(old_border, new_border, 1)

    # Ensure card wrapper is transparent
    html = html.replace('<div class="card" style="width: 100%">', '<div class="card" style="width: 100%; background: transparent; border: none;">', 1)

    return html
