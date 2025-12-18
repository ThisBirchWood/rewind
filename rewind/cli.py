#!/usr/bin/env python3
import sys
import argparse
from rewind.core import clip, mark

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewind",
        description="Control OBS recording and create instant clips",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    save = sub.add_parser("save", help="Save a section from the current recording")
    save.add_argument(
        "-s", "--seconds",
        type=int,
        default=30,
        help="Number of seconds to include in the clip (default: 30)"
    )

    mark = sub.add_parser("mark", help="Mark the current time in the recording for later reference")
    mark.add_argument(
        "-n", "--name",
        type=str,
        required=True,
        help="Name of the marker"
    )

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        clip(args.seconds)
    elif args.command == "mark":
        mark(args.name)
    else:
        parser.error("Unknown command")

    return 0

if __name__ == "__main__":
    sys.exit(main())