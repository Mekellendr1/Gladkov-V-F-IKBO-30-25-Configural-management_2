"""Visualization of the dependency graph: DOT and ASCII tree."""

from graph import CYCLE_MARKER, DEPTH_LIMIT_MARKER


def generate_dot(graph, root):
    """Generate a DOT representation of the dependency graph."""
    lines = ["digraph dependencies {"]
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box, style=filled, fillcolor=lightblue];")
    
    for node in _order(graph, root):
        children = graph.get(node, [])
        if not children:
            lines.append('    "%s" [fillcolor=lightgreen];' % node)
            continue
        for child in children:
            if child == CYCLE_MARKER:
                lines.append('    "%s" -> "CYCLE_%s" [style=dashed, color=red];' % (node, node))
                lines.append('    "CYCLE_%s" [label="(cycle)", shape=ellipse, fillcolor=yellow];' % node)
            elif child == DEPTH_LIMIT_MARKER:
                lines.append('    "%s" -> "LIMIT_%s" [style=dashed, color=gray];' % (node, node))
                lines.append('    "LIMIT_%s" [label="(depth limit)", shape=ellipse, fillcolor=lightgray];' % node)
            elif child.startswith("(error:"):
                lines.append('    "%s" -> "ERROR_%s" [style=dashed, color=orange];' % (node, node))
                lines.append('    "ERROR_%s" [label="%s", shape=ellipse, fillcolor=orange];' % (node, child))
            else:
                lines.append('    "%s" -> "%s";' % (node, child))
    
    lines.append("}")
    return "\n".join(lines)


def generate_ascii_tree(graph, root, indent="", last=True, visited=None):
    """Generate an ASCII tree representation of the dependency graph."""
    if visited is None:
        visited = set()
    
    if root in visited:
        return indent + ("└── " if last else "├── ") + root + " (cycle)\n"
    
    visited.add(root)
    children = graph.get(root, [])
    
    if not children:
        return indent + ("└── " if last else "├── ") + root + "\n"
    
    result = indent + ("└── " if last else "├── ") + root + "\n"
    
    new_indent = indent + ("    " if last else "│   ")
    
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        if child == CYCLE_MARKER:
            result += new_indent + ("└── " if is_last else "├── ") + "(cycle)\n"
        elif child == DEPTH_LIMIT_MARKER:
            result += new_indent + ("└── " if is_last else "├── ") + "(depth limit)\n"
        elif child.startswith("(error:"):
            result += new_indent + ("└── " if is_last else "├── ") + child + "\n"
        else:
            result += generate_ascii_tree(graph, child, new_indent, is_last, visited.copy())
    
    return result


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
