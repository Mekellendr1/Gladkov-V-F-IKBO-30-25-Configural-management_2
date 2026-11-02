"""Visualization of the dependency graph: DOT and ASCII tree."""

from graph import CYCLE_MARKER, DEPTH_LIMIT_MARKER


def generate_dot(graph, root):
    """Generate a DOT representation of the dependency graph."""
    lines = ["digraph dependencies {",
             "    rankdir=LR;",
             "    node [shape=box, style=filled, fillcolor=lightblue];"]
    for node in _order(graph, root):
        children = graph.get(node, [])
        if not children:
            lines.append(_leaf_line(node))
            continue
        for child in children:
            lines.extend(_edge_lines(node, child))
    lines.append("}")
    return "\n".join(lines)


def _leaf_line(node):
    """DOT line marking a leaf node."""
    return '    "%s" [fillcolor=lightgreen];' % node


def _edge_lines(node, child):
    """DOT lines for one edge from node to child."""
    if child == CYCLE_MARKER:
        return _marker_lines(node, child, "CYCLE", "(cycle)", "red", "yellow")
    if child == DEPTH_LIMIT_MARKER:
        return _marker_lines(node, child, "LIMIT",
                             "(depth limit)", "gray", "lightgray")
    if child.startswith("(error:"):
        return _marker_lines(node, child, "ERROR", child, "orange", "orange")
    return ['    "%s" -> "%s";' % (node, child)]


def _marker_lines(node, child, kind, label, edge_color, node_color):
    """DOT lines for an edge pointing to a virtual marker node."""
    vid = "%s_%s" % (kind, node)
    edge = ('    "%s" -> "%s" [style=dashed, color=%s];'
            % (node, vid, edge_color))
    vnode = ('    "%s" [label="%s", shape=ellipse, fillcolor=%s];'
             % (vid, label, node_color))
    return [edge, vnode]


def _prefix(indent, last):
    """Return the branch prefix for a node line."""
    return indent + ("└── " if last else "├── ")


def _render_children(graph, children, new_indent, visited):
    """Render all child lines of a single node."""
    lines = []
    total = len(children)
    for i, child in enumerate(children):
        is_last = (i == total - 1)
        head = _prefix(new_indent, is_last)
        if child == CYCLE_MARKER:
            lines.append(head + "(cycle)\n")
        elif child == DEPTH_LIMIT_MARKER:
            lines.append(head + "(depth limit)\n")
        elif child.startswith("(error:"):
            lines.append(head + child + "\n")
        else:
            lines.append(generate_ascii_tree(
                graph, child, new_indent, is_last, visited))
    return "".join(lines)


def generate_ascii_tree(graph, root, indent="", last=True, visited=None):
    """Generate an ASCII tree representation of the dependency graph."""
    if visited is None:
        visited = set()
    head = _prefix(indent, last)
    if root in visited:
        return head + root + " (cycle)\n"
    visited = visited | {root}
    children = graph.get(root, [])
    if not children:
        return head + root + "\n"
    new_indent = indent + ("    " if last else "│   ")
    return head + root + "\n" + _render_children(
        graph, children, new_indent, visited)


def _order(graph, root):
    """Return nodes in DFS preorder from root."""
    order = []
    seen = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in seen or node not in graph:
            continue
        seen.add(node)
        order.append(node)
        for child in reversed(graph.get(node, [])):
            if child not in seen and child in graph:
                stack.append(child)
    return order
