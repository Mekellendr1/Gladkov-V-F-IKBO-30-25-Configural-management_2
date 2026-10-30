"""Entry point of the dependency graph tool (stage 1)."""

import sys

from config import EXIT_ERROR, EXIT_OK, format_config, parse_args


def main(argv=None):
    """Print the validated configuration or an error message."""
    try:
        config = parse_args(argv)
    except ValueError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return EXIT_ERROR
    for line in format_config(config):
        print(line)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())