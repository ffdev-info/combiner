"""Combiner entry-point."""

import argparse
import asyncio
import datetime
import logging
import os
import sys
import time
import xml
from dataclasses import dataclass
from datetime import timezone
from typing import Final
from xml.dom import minidom

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

UTC_TIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"
APPNAME: Final[str] = "combiner"


@dataclass
class SignatureFormatPairing:
    internal_signature: xml.dom.minidom.Element
    file_format: xml.dom.minidom.Element


def new_prettify(dom_str):
    """Remove excess newlines from DOM output.

    via: https://stackoverflow.com/a/14493981
    """
    reparsed = minidom.parseString(dom_str)
    return "\n".join(
        [
            line
            for line in reparsed.toprettyxml(indent=" " * 2).split("\n")
            if line.strip()
        ]
    )


def get_utc_timestamp_now():
    """Get a formatted UTC timestamp for 'now' that can be used when
    a timestamp is needed.
    """
    return datetime.datetime.now(timezone.utc).strftime(UTC_TIME_FORMAT)


async def create_new_sig_file(sigs: list):
    """Create a new signature file based on the information we have
    processed.
    """
    logger.info("processing: '%s' items for a signature file", len(sigs))
    internal_sigs = [item[0] for item in sigs]
    file_formats = [item[1] for item in sigs]
    root = minidom.Document()
    signature_file = root.createElement("FFSignatureFile")
    # pylint: disable=E1101 # no attribute attributes. This seems to be
    # an incorrect read from pylint.
    signature_file.attributes["xmlns"] = (
        "http://www.nationalarchives.gov.uk/pronom/SignatureFile"
    )
    signature_file.attributes["Version"] = "1"
    signature_file.attributes["DateCreated"] = get_utc_timestamp_now()
    internal_signature_collection = root.createElement("InternalSignatureCollection")
    for item in internal_sigs:
        internal_signature_collection.appendChild(item)
    file_format_collection = root.createElement("FileFormatCollection")
    for item in file_formats:
        file_format_collection.appendChild(item)
    root.appendChild(signature_file)
    signature_file.appendChild(internal_signature_collection)
    signature_file.appendChild(file_format_collection)
    pretty_xml = root.toprettyxml(indent=" ", encoding="utf-8").decode()
    print(new_prettify(pretty_xml))


async def get_matches(node_list: xml.dom.minicompat.NodeList, identifier: str) -> list:
    """Return element matches for a given identifier"""
    ids = []
    for item in node_list:
        value = item.getElementsByTagName("InternalSignatureID")[0].firstChild.nodeValue
        if value != identifier:
            continue
        ids.append(item)
    return ids


# pylint: disable=R0914
async def split_xml(
    internal_sig_coll: xml.dom.minicompat.NodeList,
    file_format_coll: xml.dom.minicompat.NodeList,
    identifiers: list,
    prefix: str,
    start_index: int,
) -> list | list:
    """Return a separate internal signature collection and file format
    collection so that they can be recombined as a new document.
    """
    internal_signatures = internal_sig_coll[0].getElementsByTagName("InternalSignature")
    file_formats = file_format_coll[0].getElementsByTagName("FileFormat")
    bs_len = len(internal_signatures)
    ff_len = len(file_formats)
    # check determines the amount of complexity we're willing and
    # able to handle. Based on Lepore, this assert doesn't fail which
    # isn't a bad baseline.
    if bs_len != ff_len:
        return None, []
    pairings = []
    for item in internal_signatures:
        id_value = item.attributes["ID"].value
        matches = await get_matches(file_formats, id_value)
        assert len(matches) == 1
        pair = SignatureFormatPairing(item, matches[0])
        pairings.append(pair)
    ret = []
    for pair in pairings:
        idx = len(identifiers) + start_index
        identifiers.append(idx)
        pair.internal_signature.attributes["ID"] = f"{idx}"
        pair.file_format.attributes["ID"] = f"{idx}"
        pair.file_format.attributes["PUID"] = f"{prefix}/{idx}"
        pair.file_format.getElementsByTagName("InternalSignatureID")[
            0
        ].firstChild.nodeValue = idx
        ret.append((pair.internal_signature, pair.file_format))
    return ret, identifiers


async def process_paths(manifest: list, prefix: str, start_index: int):
    """Process the paths given as XML and prepare them to be combined
    into one xml.
    """
    sig_list = []
    identifiers = []
    processed = []
    manifest.sort()
    for idx, item in enumerate(manifest):
        with open(item, "r", encoding="utf8") as xml_file:
            try:
                doc = minidom.parseString(xml_file.read())
                if not doc.firstChild.tagName == "FFSignatureFile":
                    continue
                internal_sig_coll = doc.getElementsByTagName(
                    "InternalSignatureCollection"
                )
                file_format_coll = doc.getElementsByTagName("FileFormatCollection")
                res, identifiers = await split_xml(
                    internal_sig_coll,
                    file_format_coll,
                    identifiers,
                    prefix,
                    start_index,
                )
                if not res:
                    logger.error("cannot process: %s", item)
                    continue
                for pair in res:
                    sig_list.append(pair)
                processed.append(idx)
            except xml.parsers.expat.ExpatError:
                logger.error("cannot process: %s", item)
    if len(sig_list) == 0:
        logger.info("no signature files were processed")
        return
    logger.info("processed '%s' files", len(processed))
    await create_new_sig_file(sig_list)


async def create_manifest(path: str) -> list[str]:
    """Get a list of paths to process."""
    paths = []
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            logger.debug(file_path)
            paths.append(file_path)
    return paths


async def process_path(path: str, prefix: str, start_index: int):
    """Process the files at the given path."""
    logger.debug("processing files at: %s", path)
    # minidom.parseString()
    xml_paths = await create_manifest(path)
    await process_paths(xml_paths, prefix, start_index)


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
        "--prefix", help="prefix for custom puids", required=False, default="ffdev"
    )
    parser.add_argument(
        "--start-index",
        help="integer from which to start the signature index (for DROID copy-paste)",
        required=False,
        type=int,
        default=1,
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
            prefix=args.prefix,
            start_index=args.start_index,
        )
    )


if __name__ == "__main__":
    main()
