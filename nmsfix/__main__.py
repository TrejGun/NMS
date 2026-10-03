import argparse
import sys

from nmsfix import __version__
from nmsfix.errors import PatchError
from nmsfix.workflow import install, restore


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install or remove the Mac No Man's Sky aerial-scan patch."
    )
    parser.add_argument("action", nargs="?", choices=("install", "restore"), default="install")
    parser.add_argument("--restore", action="store_true", help="Put the original archives back.")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if args.restore or args.action == "restore":
            restore()
        else:
            install()
    except PatchError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
