"""Render a bounded interactive PyVis graph around the discovered route."""

from html import escape

from pyvis.network import Network

from .search_types import SearchResult


def graph_html(result: SearchResult) -> str:
    graph = Network(height="540px", width="100%", directed=True, cdn_resources="in_line")
    graph.barnes_hut()
    path = result.path
    path_edges = set(zip(path, path[1:]))
    edges = set(result.edges) | path_edges
    nodes = set(path)
    for source, target in edges:
        nodes.add(source)
        nodes.add(target)
    for node in nodes:
        if node == result.start:
            color, size = "#2563eb", 28
        elif node == result.target:
            color, size = "#f97316", 28
        elif node in path:
            color, size = "#22c55e", 23
        else:
            color, size = "#cbd5e1", 12
        graph.add_node(node, label=node, title=escape(node), color=color, size=size)
    for source, target in edges:
        highlight = (source, target) in path_edges
        graph.add_edge(source, target, color="#16a34a" if highlight else "#cbd5e1",
                       width=4 if highlight else 1, arrows="to")
    return graph.generate_html(notebook=False)
