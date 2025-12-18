#!/usr/bin/env python3
import sys
import argparse
from rewind.core import clip, mark, print_markers

def build_save_parser(subparsers: argparse._SubParsersAction) -> None:
    save_parser = subparsers.add_parser("save", help="Save a section from the current recording")
    save_parser.add_argument(
        "-s", "--seconds",
        type=int,
        default=30,
        help="Number of seconds to include in the clip (default: 30)"
    )

def build_mark_parser(subparsers: argparse._SubParsersAction) -> None:
    mark_parser = subparsers.add_parser("mark", help="Mark the current time in the recording for later reference")
    mark_parser.add_argument(
        "-n", "--name",
        type=str,
        required=True,
        help="Name of the marker"
    )

def build_list_parser(subparsers: argparse._SubParsersAction) -> None:
    list_parser = subparsers.add_parser("list", help="List all markers in the recording")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewind",
        description="Control OBS recording and create instant clips",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    build_save_parser(sub)
    build_mark_parser(sub)
    build_list_parser(sub)

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        clip(args.seconds)
    elif args.command == "mark":
        mark(args.name)
    elif args.command == "list":
        print_markers()
    else:
        parser.error("Unknown command")

    return 0

if __name__ == "__main__":
    sys.exit(main())