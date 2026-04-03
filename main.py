import argparse
import json
import sys

import store


def cmd_dump(args):
    """print raw store"""
    db = store.load()
    target = args.what  # authors | books | all
    if target in ("authors", "books"):
        print(json.dumps(db[target], indent=2))
    else:
        print(json.dumps(db, indent=2))




def build_parser() -> argparse.ArgumentParser:    
    p = argparse.ArgumentParser(prog="arkiv", description="book collection manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    # dump — handy while building out the rest
    d = sub.add_parser("dump", help="print store contents")
    d.add_argument("what", nargs="?", default="all", choices=["all", "authors", "books"])
    d.set_defaults(func=cmd_dump)

    return p


def main():
    parser = build_parser()          # registers subcommands
    args = parser.parse_args()       # matches user input to subcommand
    args.func(args)                  # calls the bound function (e.g. cmd_dump)


if __name__ == "__main__":
    main()
