#!/usr/bin/env python3
from datetime import datetime
from rewind.video import clip

import obsws_python as obs
import sys, argparse

command = sys.argv[1] if len(sys.argv) > 1 else None

def start_recording(con):
    con.start_record()
    print("Started recording")

def stop_recording(con):
    con.stop_record()
    print("Stopped recording")

def create_clip(con):
    record_dir = con.get_record_directory()
    output_file_name = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    clip(record_dir.record_directory, output_file_name)
    print(f"Created clip: {output_file_name}")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="rewind",
        description="Control OBS recording and create instant clips",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("start", help="Start OBS recording")
    sub.add_parser("stop", help="Stop OBS recording")
    sub.add_parser("clip", help="Create a clip from the current recording")

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    con = obs.ReqClient()

    try:
        if args.command == "start":
            start_recording(con)
        elif args.command == "stop":
            stop_recording(con)
        elif args.command == "clip":
            create_clip(con)
        else:
            parser.error("Unknown command")

    finally:
        con.disconnect()


if __name__ == "__main__":
    sys.exit(main())