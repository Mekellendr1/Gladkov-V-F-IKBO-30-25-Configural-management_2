"""Configuration handling for the dependency graph tool."""

import argparse
import os
import re
from urllib.parse import urlparse

DEFAULT_VERSION = "1.0.0"
DEFAULT_MAX_DEPTH = 5
DEPTH_MIN = 1
DEPTH_MAX = 99
EXIT_OK = 0
EXIT_ERROR = 2
URL_SCHEMES = ("http", "https")
PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


def build_parser():
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Dependency graph visualization tool",
    )
    parser.add_argument("--package", required=True,
                        help="name of the analyzed package")
    parser.add_argument("--source", required=True,
                        help="repository URL or test graph file path")
    parser.add_argument("--test-mode", action="store_true",
                        help="read graph from a local test file")
    parser.add_argument("--version", default=DEFAULT_VERSION,
                        help="package version (default: %(default)s)")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="print dependencies as an ASCII tree")
    parser.add_argument("--load-order", action="store_true",
                        help="print the dependency load order")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH,
                        help="maximum analysis depth (default: %(default)s)")
    return parser


def validate_package(value):
    """Validate the package name option."""
    name = value.strip()
    if not name:
        raise ValueError("package name must not be empty")
    if not PACKAGE_PATTERN.match(name):
        raise ValueError("package name contains illegal characters")
    return name


def validate_source(value, test_mode):
    """Validate the repository source option."""
    source = value.strip()
    if not source:
        raise ValueError("source must not be empty")
    if test_mode:
        if not os.path.isfile(source):
            raise ValueError("test graph file not found: " + source)
        return source
    parsed = urlparse(source)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ValueError("source must be a valid http(s) URL")
    return source


def validate_version(value):
    """Validate the package version option."""
    version = value.strip()
    if not VERSION_PATTERN.match(version):
        raise ValueError("version must look like X.Y.Z")
    return version


def validate_max_depth(value):
    """Validate the maximum depth option."""
    if value < DEPTH_MIN or value > DEPTH_MAX:
        raise ValueError("max depth must be within %d..%d"
                         % (DEPTH_MIN, DEPTH_MAX))
    return value


def parse_args(argv=None):
    """Parse and validate command line arguments."""
    args = build_parser().parse_args(argv)
    config = {"test_mode": bool(args.test_mode),
              "ascii_tree": bool(args.ascii_tree)}
    config["package"] = validate_package(args.package)
    config["source"] = validate_source(args.source, config["test_mode"])
    config["version"] = validate_version(args.version)
    config["max_depth"] = validate_max_depth(args.max_depth)
    config["load_order"] = bool(args.load_order)
    return config


CONFIG_KEYS = ("package", "source", "test_mode",
               "version", "ascii_tree", "max_depth")


def format_config(config):
    """Render the configuration as key-value lines."""
    return ["%s = %s" % (key, config[key]) for key in CONFIG_KEYS]
