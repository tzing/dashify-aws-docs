from __future__ import annotations

import dataclasses
import enum
import json
import logging
import re
import shutil
import sqlite3
import typing
import urllib.parse
from contextlib import closing
from pathlib import Path

import bs4
import click
import lxml.etree
import tqdm

if typing.TYPE_CHECKING:
    from click.core import Context, Parameter

logger = logging.getLogger(__name__)
regex_ws = re.compile(r"\s+")


@click.group("dashify")
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode.")
def entry(verbose: bool):
    """Entry point for dashify commands."""
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )


class URL(click.ParamType):
    """URL type for click."""

    name = "url"

    def convert(self, value: str, param: Parameter | None, ctx: Context | None) -> str:
        if not value.startswith("https://docs.aws.amazon.com/"):
            logger.warning("The input URL is not an AWS doc page: %s", value)
        value = value.rstrip("/") + "/"
        return value


def prepare_docset(docset_path: Path):
    """Prepare docset folder structure."""
    current_dir = Path(__file__).resolve().parent

    # normalize output path
    if docset_path.suffix != ".docset":
        docset_path = docset_path.parent / f"{docset_path.name}.docset"
        logger.info(f"Output path is not a docset, using '{docset_path}'")

    if docset_path.is_dir() and any(docset_path.iterdir()):
        logger.error(f"Output directory '{docset_path}' is not empty")
        raise click.Abort

    # css
    css_destination = docset_path / "Contents" / "Resources" / "Documents" / "Css"
    css_destination.mkdir(parents=True, exist_ok=True)

    css_source = current_dir / "statics" / "css"
    shutil.copy(css_source / "normalize.css", css_destination)
    shutil.copy(css_source / "aws-doc-page.css", css_destination)

    # images
    images_destination = docset_path / "Contents" / "Resources" / "Documents" / "Images"
    images_destination.mkdir(parents=True, exist_ok=True)

    logger.debug("Docset folder structure created: %s", docset_path)

    return docset_path


def iter_document_files(site_url: str, root_dir: Path):
    """Iterate over document files."""
    document_dir = root_dir / urllib.parse.urlsplit(site_url).path[1:]
    logger.debug("Document directory: %s", document_dir)

    doc_files = list(document_dir.glob("*.html"))
    logger.info("%d docs to be converted", len(doc_files))

    for path in tqdm.tqdm(doc_files):
        yield path


@dataclasses.dataclass
class DocMetadata:
    title: str
    breadcrumb_text: list[str]
    breadcrumb_url: list[str]


def extract_metadata(soup: bs4.BeautifulSoup) -> DocMetadata | None:
    """Extract metadata from doc."""
    # title
    title_elem = soup.find("h1")
    if not title_elem:
        return

    title = sanitize(title_elem.text)

    # breadcrumb
    breadcrumb_elem = soup.find("script", type="application/ld+json")
    breadcrumb_cfg = json.loads(breadcrumb_elem.text)
    breadcrumb_items = breadcrumb_cfg["itemListElement"]

    breadcrumb_text = [item["name"] for item in breadcrumb_items]
    breadcrumb_url = [item["item"] for item in breadcrumb_items]

    return DocMetadata(
        title=title,
        breadcrumb_text=breadcrumb_text,
        breadcrumb_url=breadcrumb_url,
    )


def sanitize(s: str) -> str:
    return regex_ws.sub(" ", s)


def convert(
    *,
    file_path: Path,
    soup: bs4.BeautifulSoup,
    root_dir: Path,
    docset_path: Path,
    site_url: str,
):
    """Clean up the HTML and convert it to Dash docset format."""
    # drop assets
    for node in soup.find_all("script"):
        node.decompose()
    for node in soup.find_all("link"):
        node.decompose()

    # add stylesheet
    soup.head.extend(
        [
            soup.new_tag("link", href="Css/normalize.css", rel="stylesheet"),
            soup.new_tag("link", href="Css/aws-doc-page.css", rel="stylesheet"),
        ]
    )

    # fix links
    for node in soup.find_all("a"):
        target = get_alt_target(node["href"], site_url, root_dir)
        if isinstance(target, str):
            node["href"] = urllib.parse.urljoin(site_url, node["href"])

    # fix images
    img_dir = docset_path / "Contents" / "Resources" / "Documents" / "Images"
    for node in soup.find_all("img"):
        target = get_alt_target(node["src"], site_url, root_dir)
        if isinstance(target, str):
            node["src"] = urllib.parse.urljoin(site_url, node["src"])
        else:
            node["src"] = f"Images/{target.name}"
            shutil.copy(target, img_dir)
            logger.debug("Copy %s to %s", target, img_dir / target.name)

    # write to file
    doc_path = docset_path / "Contents" / "Resources" / "Documents" / file_path.name
    doc_path.write_text(str(soup))
    logger.debug("Write to %s", doc_path)


def get_alt_target(path: str, site_url: str, root_dir: Path):
    if path.startswith(("https://", "http://")):
        return path

    fallback = urllib.parse.urljoin(site_url, path)
    alt = root_dir / urllib.parse.urlsplit(fallback).path[1:]
    if alt.exists():
        return alt
    else:
        return fallback


def create_docset_index(docset_path: Path, indexes: list[dict[str, str]]):
    """Create `docSet.dsidx` file."""
    logger.debug("Building docset index")

    sqlite3.paramstyle = "named"

    db_path = docset_path / "Contents" / "Resources" / "docSet.dsidx"
    db = sqlite3.connect(db_path)

    # schema
    with closing(db.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE searchIndex(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                path TEXT,
                UNIQUE(name, type, path)
            );
            """
        )

    # data
    with closing(db.cursor()) as cur:
        cur.executemany(
            """
            INSERT INTO searchIndex(name, type, path)
            VALUES
            (:name, :type, :path);
            """,
            indexes,
        )

    db.commit()
    logger.debug(f"Created docset index: {db_path}")


def copy_icons(icon_dir_name: str, docset_path: Path):
    icon_dir = Path(__file__).resolve().parent / "statics" / icon_dir_name
    shutil.copy(icon_dir / "icon.png", docset_path)
    shutil.copy(icon_dir / "icon@2x.png", docset_path)


def create_info_plist(docset_path: Path, metadata: dict):
    """Create Info.plist file."""
    # build tree
    info_plist = lxml.etree.Element("plist", version="1.0")
    info_dict = lxml.etree.SubElement(info_plist, "dict")

    for key, value in metadata.items():
        lxml.etree.SubElement(info_dict, "key").text = key
        lxml.etree.SubElement(info_dict, "string").text = value

    lxml.etree.SubElement(info_dict, "key").text = "isDashDocset"
    lxml.etree.SubElement(info_dict, "true")

    tree = lxml.etree.ElementTree(info_plist)

    # output
    info_plist_path = docset_path / "Contents" / "Info.plist"
    with info_plist_path.open("wb") as fd:
        fd.write(
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        )
        tree.write(fd, pretty_print=True)

    logger.debug("Created Info.plist file: %s", info_plist_path)


class EntryType(enum.StrEnum):
    """Supported entry types

    https://kapeli.com/docsets#supportedentrytypes
    """

    Annotation = "Annotation"
    Attribute = "Attribute"
    Binding = "Binding"
    Builtin = "Builtin"
    Callback = "Callback"
    Category = "Category"
    Class = "Class"
    Command = "Command"
    Component = "Component"
    Constant = "Constant"
    Constructor = "Constructor"
    Define = "Define"
    Delegate = "Delegate"
    Diagram = "Diagram"
    Directive = "Directive"
    Element = "Element"
    Entry = "Entry"
    Enum = "Enum"
    Environment = "Environment"
    Error = "Error"
    Event = "Event"
    Exception = "Exception"
    Extension = "Extension"
    Field = "Field"
    File = "File"
    Filter = "Filter"
    Framework = "Framework"
    Function = "Function"
    Global = "Global"
    Guide = "Guide"
    Hook = "Hook"
    Instance = "Instance"
    Instruction = "Instruction"
    Interface = "Interface"
    Keyword = "Keyword"
    Library = "Library"
    Literal = "Literal"
    Macro = "Macro"
    Method = "Method"
    Mixin = "Mixin"
    Modifier = "Modifier"
    Module = "Module"
    Namespace = "Namespace"
    Notation = "Notation"
    Object = "Object"
    Operator = "Operator"
    Option = "Option"
    Package = "Package"
    Parameter = "Parameter"
    Plugin = "Plugin"
    Procedure = "Procedure"
    Property = "Property"
    Protocol = "Protocol"
    Provider = "Provider"
    Provisioner = "Provisioner"
    Query = "Query"
    Record = "Record"
    Resource = "Resource"
    Sample = "Sample"
    Section = "Section"
    Service = "Service"
    Setting = "Setting"
    Shortcut = "Shortcut"
    Statement = "Statement"
    Struct = "Struct"
    Style = "Style"
    Subroutine = "Subroutine"
    Tag = "Tag"
    Test = "Test"
    Trait = "Trait"
    Type = "Type"
    Union = "Union"
    Value = "Value"
    Variable = "Variable"
    Word = "Word"
