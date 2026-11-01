"""Dependency graph construction with DFS, depth limit and cycles."""

CYCLE_MARKER = "(cycle)"
DEPTH_LIMIT_MARKER = "(depth limit)"


def build_graph(fetch_deps, root, max_depth):
    """Build the dependency graph by recursive DFS."""
    graph = {}
    visiting = set()
    root_children = _visit(graph, visiting, fetch_deps, root, 0, max_depth)
    graph[root] = root_children
    return graph


def _visit(graph, visiting, fetch_deps, package, depth, max_depth):
    """Visit one node and return list of children labels for parent."""
    if package in graph:
        return [package]
    if package in visiting:
        return [CYCLE_MARKER]
    if depth >= max_depth:
        return [DEPTH_LIMIT_MARKER]
    visiting.add(package)
    try:
        deps = fetch_deps(package)
    except Exception as error:
        visiting.discard(package)
        return ["(error: %s)" % error]
    children = []
    for dep in deps:
        dep_id = dep.get("id")
        if not dep_id:
            continue
        child_label = _visit(graph, visiting, fetch_deps, dep_id, depth + 1, max_depth)
        if dep_id not in graph and dep_id not in visiting:
            graph[dep_id] = child_label
        children.extend(child_label)
    visiting.discard(package)
    return [package]