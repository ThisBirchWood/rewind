#!/usr/bin/env python3
from datetime import datetime
from rewind.video import combine_last_x_ts_files
import obsws_python as obs
import sys, argparse

def create_recording(seconds: int) -> None:
    output_file_name = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    combine_last_x_ts_files(seconds, output_file_name)
    print(f"Created clip: {output_file_name}")

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

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        create_recording(args.seconds)
    else:
        parser.error("Unknown command")

    return 0

if __name__ == "__main__":
    sys.exit(main())