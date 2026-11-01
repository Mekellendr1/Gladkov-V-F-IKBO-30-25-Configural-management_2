"""Topological sort of the dependency graph."""

from graph import CYCLE_MARKER, DEPTH_LIMIT_MARKER


def is_marker(label):
    """Return True if the label is not a real package node."""
    if label in (CYCLE_MARKER, DEPTH_LIMIT_MARKER):
        return True
    if isinstance(label, str) and label.startswith("(error:"):
        return True
    return False


def load_order(graph, root):
    """Return packages in load order (dependencies first, root last)."""
    result = []
    temp_mark = set()
    perm_mark = set()

    def visit(node):
        """Perform DFS and append node on exit."""
        if node in perm_mark:
            return
        if node in temp_mark:
            return
        temp_mark.add(node)
        for child in graph.get(node, []):
            if is_marker(child):
                continue
            if child not in graph:
                continue
            visit(child)
        temp_mark.discard(node)
        perm_mark.add(node)
        result.append(node)

    if root in graph:
        visit(root)
    return result