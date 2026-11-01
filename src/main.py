"""Entry point of the dependency graph tool (stage 3)."""

import json
import sys

from config import EXIT_ERROR, EXIT_OK, parse_args
from graph import CYCLE_MARKER, build_graph
from nuget import (
    NuGetError,
    fetch_json,
    fetch_nuspec,
    find_package_base_url,
    parse_dependencies,
)


def make_nuget_fetcher(config):
    """Return a cached function fetching direct deps from NuGet."""
    service_index = fetch_json(config["source"])
    package_base = find_package_base_url(service_index)
    cache = {}

    def fetch(package):
        """Fetch direct dependencies of one NuGet package."""
        if package not in cache:
            nuspec = fetch_nuspec(package_base, package,
                                  config["version"])
            cache[package] = parse_dependencies(nuspec)
        return cache[package]

    return fetch


def make_test_fetcher(config):
    """Return a function fetching direct deps from a test graph."""
    try:
        with open(config["source"], "r", encoding="utf-8") as stream:
            graph = json.load(stream)
    except json.JSONDecodeError:
        raise ValueError("test graph file is not valid JSON")
    except OSError:
        raise ValueError("cannot read test graph file")
    if not isinstance(graph, dict):
        raise ValueError("test graph must be a JSON object")
    for package, deps in graph.items():
        if not isinstance(deps, list):
            raise ValueError("deps of %s must be a list" % package)
        for dep in deps:
            if not isinstance(dep, dict):
                raise ValueError("dep of %s must be an object" % package)
            if not isinstance(dep.get("id"), str) or not dep.get("id"):
                raise ValueError("dep of %s must have string id"
                                 % package)

    def fetch(package):
        """Fetch direct dependencies from the test graph."""
        deps = graph.get(package)
        if deps is None:
            raise ValueError("package %s not found in test graph"
                             % package)
        return deps

    return fetch


def print_graph(graph, root):
    """Print the dependency graph as `node -> child` lines."""
    for node in _graph_order(graph, root):
        children = graph.get(node, [])
        if not children:
            print("%s -> (none)" % node)
            continue
        for child in children:
            print("%s -> %s" % (node, child))


def _graph_order(graph, root):
    """Return real graph nodes in DFS preorder from root."""
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


def main(argv=None):
    """Build the dependency graph and print it or an error."""
    try:
        config = parse_args(argv)
        if config["test_mode"]:
            fetch = make_test_fetcher(config)
        else:
            fetch = make_nuget_fetcher(config)
        graph = build_graph(fetch, config["package"],
                            config["max_depth"])
    except ValueError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    except NuGetError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    print_graph(graph, config["package"])
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())