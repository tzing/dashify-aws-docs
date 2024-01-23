from __future__ import annotations

import logging
import urllib.parse
from pathlib import Path

import bs4
import click

import dashify.core

METADATA = {
    "CFBundleIdentifier": "aws-redshift-dg",
    "DocSetPlatformFamily": "Amazon Redshift",
    "dashIndexFilePath": "welcome.html",
}

logger = logging.getLogger(__name__)


@dashify.core.entry.command()
@click.option(
    "-t",
    "--title",
    default="Amazon Redshift Database Developer Guide",
    show_default=True,
    help="Docset title",
)
@click.option(
    "-u",
    "--site-url",
    metavar="URL",
    type=dashify.core.URL(),
    default="https://docs.aws.amazon.com/redshift/latest/dg/",
    show_default=True,
    help="URL of the document site. This is used to resolve file path and relative links.",
)
@click.option(
    "-r",
    "--root-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="./docs.aws.amazon.com",
    show_default=True,
    help="Root directory that contains the downloaded docs",
)
@click.option(
    "-d",
    "--docset-path",
    metavar="DOCSET",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to output docset",
)
def redshift(title: str, site_url: str, root_dir: Path, docset_path: Path):
    """Convert RedShift documents to docsets."""
    docset_path = dashify.core.prepare_docset(docset_path)
    logger.info(f"Convert RedShift docs from '{root_dir}' to '{docset_path}'")

    indexes = []
    for doc_file in dashify.core.iter_document_files(site_url, root_dir):
        logger.debug("Convert %s", doc_file)
        soup = bs4.BeautifulSoup(doc_file.read_text(), "lxml")

        # extract metadata
        metadata = dashify.core.extract_metadata(soup)
        if not metadata:
            logger.warning("No metadata found for %s", doc_file)
            continue

        # convert doc
        dashify.core.convert(
            file_path=doc_file,
            soup=soup,
            root_dir=root_dir,
            docset_path=docset_path,
            site_url=site_url,
        )

        # add to index
        doc_type = assign_doc_type(
            site_url=site_url, breadcrumb_url=metadata.breadcrumb_url
        )
        indexes.append(
            {
                "name": metadata.title,
                "type": doc_type,
                "path": doc_file.name,
            }
        )

    dashify.core.create_docset_index(docset_path, indexes)

    # finalise
    METADATA["CFBundleName"] = title
    METADATA["DashDocSetFallbackURL"] = site_url
    dashify.core.create_info_plist(docset_path, METADATA)
    dashify.core.copy_icons("redshift-icons", docset_path)

    # done
    logger.info("Done! Docset created at %s", docset_path)


def assign_doc_type(*, site_url: str, breadcrumb_url: list[str]) -> str:
    """
    Assign doc type based on breadcrumb URL.

    Found that using URL make this function more robust and make it easier to
    share the code with the docs in other languages.

    Last updated
    ------------
    This function is written in 2024-01-15
    """
    site_base = Path(urllib.parse.urlsplit(site_url).path)

    # the first 3 items are always the same
    nav = []
    for item_url in breadcrumb_url[3:]:
        item_path = Path(urllib.parse.urlsplit(item_url).path)
        nav.append(str(item_path.relative_to(site_base)))

    # assign doc type based on breadcrumb
    EntryType = dashify.core.EntryType

    match nav[:1]:
        case ["cm_chap_system-tables.html"]:  # System tables and views reference
            return EntryType.Builtin
        case ["cm_chap_ConfigurationRef.html"]:  # Configuration reference
            return EntryType.Setting
        case ["c_sampledb.html"]:  # Sample database
            return EntryType.Builtin

    PATH_SQL_CMD_REF = "cm_chap_SQLCommandRef.html"  # SQL commands reference
    match nav[:2]:
        case [PATH_SQL_CMD_REF, "c_SQL_commands.html"]:  # SQL commands reference
            return EntryType.Command
        case [PATH_SQL_CMD_REF, "c_SQL_functions.html"]:  # SQL functions reference
            return EntryType.Function
        case [PATH_SQL_CMD_REF, "r_pg_keywords.html"]:  # Reserved words
            return EntryType.Keyword

    PATH_USING_SQL = "c_SQL_reference.html"  # Using SQL
    match nav[:3]:
        case [PATH_SQL_CMD_REF, PATH_USING_SQL, "r_expressions.html"]:  # Expressions
            return EntryType.Statement
        case [PATH_SQL_CMD_REF, PATH_USING_SQL, "r_conditions.html"]:  # Conditions
            return EntryType.Statement

    if nav[:4] == [
        PATH_SQL_CMD_REF,
        PATH_USING_SQL,
        "c_Basic_elements.html",
        "c_Supported_data_types.html",
    ]:
        return EntryType.Type

    # fallback to 'Guide'
    return EntryType.Guide
