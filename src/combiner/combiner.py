"""Combiner entry-point."""

import argparse
import asyncio
import logging
import sys
import time
from typing import Final

try:
    import version
except ModuleNotFoundError:
    try:
        from src.combiner import version
    except ModuleNotFoundError:
        pass


# Set up logging.
logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",  # noqa: E501
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Format logs using UTC time.
logging.Formatter.converter = time.gmtime


logger = logging.getLogger(__name__)

APPNAME: Final[str] = "combiner"


async def process_path(path: str):
    """Process the files at the given path."""
    logger.debug("processing files at: %s", path)


def main() -> None:
    """Primary entry point for this script."""
    parser = argparse.ArgumentParser(
        prog="combiner",
        description="combine development signature files into one",
        epilog="for more information visit https://github.com/ffdev-info/combiner",
    )
    parser.add_argument(
        "--debug",
        help="use debug loggng",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--path",
        help="directory where the signature files are",
        required=False,
    )
    parser.add_argument(
        "--version",
        help="print version information",
        required=False,
        action="store_true",
    )
    args = parser.parse_args()
    logging.getLogger(__name__).setLevel(logging.DEBUG if args.debug else logging.INFO)
    logger.debug("debug logging is configured")
    if args.version:
        print(f"{APPNAME}: {version.get_version()}")
        sys.exit()
    if not args.path:
        parser.print_help(sys.stderr)
        sys.exit()
    asyncio.run(
        process_path(
            path=args.path,
        )
    )


if __name__ == "__main__":
    main()
