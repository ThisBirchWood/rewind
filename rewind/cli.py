#!/usr/bin/env python3
import sys
import argparse

from rewind.core import clip, mark, save, print_markers
from rewind.autostart import install
from rewind.config import Config

def build_clip_parser(subparsers: argparse._SubParsersAction) -> None:
    clip_parser = subparsers.add_parser("clip", help="Clips the last 'x' seconds")
    clip_parser.add_argument(
        "-s", "--seconds",
        type=int,
        default=60,
        help="Number of seconds to include in the clip (default: 60)"
    )

def build_save_parser(subparsers: argparse._SubParsersAction) -> None:
    save_parser = subparsers.add_parser("save", help="Saves a segment between any two markers")
    save_parser.add_argument(
        "-s", "--start",
        type=str,
        required=True,
        help="Marker to begin the recording from"
    )

    save_parser.add_argument(
        "-e", "--end",
        type=str,
        required=True,
        help="Marker to end the recording from"
    )

def build_mark_parser(subparsers: argparse._SubParsersAction) -> None:
    mark_parser = subparsers.add_parser("mark", help="Mark the current time in the recording for later reference")
    mark_parser.add_argument(
        "-n", "--name",
        type=str,
        required=False,
        help="Name of the marker"
    )

def build_list_parser(subparsers: argparse._SubParsersAction) -> None:
    list_parser = subparsers.add_parser("list", help="List all markers in the recording")

def build_install_parser(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser(
        "install",
        help="Enable background recording daemon",
        description="Install and enable the rewind daemon using system autostart."
    )

def build_config_parser(subparsers: argparse._SubParsersAction) -> None:
    config_parser = subparsers.add_parser("config", help="View or edit config values")
    config_sub = config_parser.add_subparsers(dest="config_command")

    get_parser = config_sub.add_parser("get", help="Print a single config value")
    get_parser.add_argument("key", help="Dotted key, e.g. obs.host")

    set_parser = config_sub.add_parser("set", help="Update a config value")
    set_parser.add_argument("key", help="Dotted key, e.g. obs.host")
    set_parser.add_argument("value", help="New value")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewind",
        description="Control OBS recording and create instant clips",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    build_clip_parser(sub)
    build_mark_parser(sub)
    build_list_parser(sub)
    build_save_parser(sub)
    build_install_parser(sub)
    build_config_parser(sub)

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = Config()

    try:
        if args.command == "clip":
            clip(args.seconds)
        elif args.command == "mark":
            mark(args.name)
        elif args.command == "list":
            print_markers()
        elif args.command == "save":
            save(args.start, args.end)
        elif args.command == "install":
            install()
        elif args.command == "config":
            if args.config_command == "set":
                cfg.set(args.key, args.value)
            elif args.config_command == "get":
                print(cfg.get(args.key))
            else:
                parser.error("Unknown config command: expected 'get' or 'set'")
        else:
            parser.error("Unknown command")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
