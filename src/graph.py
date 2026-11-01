"""Dependency graph construction with DFS, depth limit and cycles."""

CYCLE_MARKER = "(cycle)"
DEPTH_LIMIT_MARKER = "(depth limit)"


def build_graph(fetch_deps, root, max_depth):
    """Build the dependency graph by recursive DFS.

    Raises ValueError when the root package cannot be fetched.
    """
    graph = {}
    on_path = set()
    problem = _visit(graph, on_path, fetch_deps, root, 0, max_depth)
    if problem is not None:
        raise ValueError(problem)
    return graph


def _visit(graph, on_path, fetch_deps, package, depth, max_depth):
    """Fill graph[package]; return cycle marker, error text or None."""
    if package in graph:
        return None
    if package in on_path:
        return CYCLE_MARKER
    if depth >= max_depth:
        graph[package] = [DEPTH_LIMIT_MARKER]
        return None
    on_path.add(package)
    try:
        deps = fetch_deps(package)
    except Exception as error:
        on_path.discard(package)
        return str(error)
    children = []
    for dep in deps:
        dep_id = dep.get("id")
        if not dep_id:
            continue
        result = _visit(
            graph, on_path, fetch_deps, dep_id, depth + 1, max_depth)
        if result is None:
            children.append(dep_id)
        elif result == CYCLE_MARKER:
            children.append(CYCLE_MARKER)
        else:
            children.append("(error: %s)" % result)
    graph[package] = children
    on_path.discard(package)
    return None