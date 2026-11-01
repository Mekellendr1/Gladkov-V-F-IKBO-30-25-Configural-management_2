"""Dependency graph construction with DFS, depth limit and cycles."""

CYCLE_MARKER = "(cycle)"
DEPTH_LIMIT_MARKER = "(depth limit)"


def build_graph(fetch_deps, root, max_depth):
    """Build the dependency graph by recursive DFS.

    fetch_deps(package) returns direct dependencies as a list of
    dicts with key "id". Cycles are cut with CYCLE_MARKER and the
    depth limit is marked with DEPTH_LIMIT_MARKER.
    """
    graph = {}
    visiting = set()
    _visit(graph, visiting, fetch_deps, root, 0, max_depth)
    return graph


def _visit(graph, visiting, fetch_deps, package, depth, max_depth):
    """Visit one node and recurse into its dependencies."""
    if package in graph:
        return
    if package in visiting:
        graph[package] = [CYCLE_MARKER]
        return
    if depth >= max_depth:
        graph[package] = [DEPTH_LIMIT_MARKER]
        return
    visiting.add(package)
    try:
        deps = fetch_deps(package)
    except Exception as error:
        graph[package] = ["(error: %s)" % error]
        visiting.discard(package)
        return
    children = []
    for dep in deps:
        dep_id = dep.get("id")
        if not dep_id:
            continue
        children.append(dep_id)
        _visit(graph, visiting, fetch_deps, dep_id, depth + 1, max_depth)
    graph[package] = children
    visiting.discard(package)