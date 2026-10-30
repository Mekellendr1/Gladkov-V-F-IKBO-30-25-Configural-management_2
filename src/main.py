"""Entry point of the dependency graph tool (stage 2)."""

import json
import sys

from config import EXIT_ERROR, EXIT_OK, parse_args
from nuget import (
    NuGetError,
    fetch_json,
    fetch_nuspec,
    find_package_base_url,
    parse_dependencies,
)


def normalize_deps(raw):
    """Validate and normalize a raw dependency list."""
    if not isinstance(raw, list):
        raise ValueError("dependency list must be an array")
    deps = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("dependency entry must be an object")
        if not isinstance(item.get("id"), str) or not item.get("id"):
            raise ValueError("dependency entry must contain string id")
        version = item.get("version", "")
        if not isinstance(version, str):
            raise ValueError("dependency version must be a string")
        deps.append({"id": item["id"], "version": version})
    return deps


def fetch_nuget_dependencies(config):
    """Return direct dependencies from a NuGet repository."""
    service_index = fetch_json(config["source"])
    package_base = find_package_base_url(service_index)
    nuspec = fetch_nuspec(package_base,
                          config["package"],
                          config["version"])
    return parse_dependencies(nuspec)


def fetch_test_dependencies(config):
    """Return direct dependencies from a local test graph file."""
    try:
        with open(config["source"], "r", encoding="utf-8") as stream:
            graph = json.load(stream)
    except json.JSONDecodeError:
        raise ValueError("test graph file is not valid JSON")
    except OSError:
        raise ValueError("cannot read test graph file")
    versions = graph.get(config["package"])
    if not isinstance(versions, dict):
        raise ValueError("package %s not found in test graph"
                         % config["package"])
    deps = versions.get(config["version"])
    if deps is None:
        raise ValueError("package %s %s not found in test graph"
                         % (config["package"], config["version"]))
    return normalize_deps(deps)


def print_dependencies(deps):
    """Print direct dependencies as `id version` lines."""
    if not deps:
        print("(no dependencies)")
        return
    for dep in deps:
        print("%s %s" % (dep["id"], dep["version"] or ""))


def main(argv=None):
    """Print direct dependencies or an error message."""
    try:
        config = parse_args(argv)
        if config["test_mode"]:
            deps = fetch_test_dependencies(config)
        else:
            deps = fetch_nuget_dependencies(config)
    except ValueError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    except NuGetError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    print_dependencies(deps)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())