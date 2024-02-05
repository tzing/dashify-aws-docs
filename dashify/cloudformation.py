from __future__ import annotations

import logging
from pathlib import Path

import bs4
import click

import dashify.core

METADATA = {
    "CFBundleIdentifier": "aws-cloudformation-ug",
    "DocSetPlatformFamily": "AWS CloudFormation",
    "dashIndexFilePath": "Welcome.html",
}

logger = logging.getLogger(__name__)


@dashify.core.entry.command()
@click.option(
    "-t",
    "--title",
    default="AWS CloudFormation User Guide",
    show_default=True,
    help="Docset title",
)
@click.option(
    "-u",
    "--site-url",
    type=dashify.core.URL(),
    default="https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/",
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
def cloudformation(title: str, site_url: str, root_dir: Path, docset_path: Path):
    """Convert CloudFormation documents to docsets."""
    docset_path = dashify.core.prepare_docset(docset_path)
    logger.info(f"Convert CloudFormation docs from '{root_dir}' to '{docset_path}'")

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

        if override := override_doc_type(metadata):
            doc_type = override
        else:
            doc_type = detect_doc_type(doc_file)

        # add to index
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
    dashify.core.copy_icons("cloudformation-icons", docset_path)

    # done
    logger.info("Done! Docset created at %s", docset_path)


def detect_doc_type(path: Path) -> str:
    """Detect doc type based on file name.

    Last updated
    ------------
    2024-02-05
    """
    EntryType = dashify.core.EntryType

    if path.stem.startswith(("AWS_", "Alexa_")):
        return EntryType.Namespace

    words = path.stem.split("-")

    match words[:5]:
        case ["intrinsic", "function", "reference", "foreach", "example"]:
            return EntryType.Sample
        case ["intrinsic", "function", "reference", "foreach", "examples"]:
            return EntryType.Sample

    match words[:3]:
        case ["crpg", "ref", "requests"]:
            return EntryType.Object
        case ["crpg", "ref", "responses"]:
            return EntryType.Object
        case ["crpg", "ref", "requesttypes"]:
            if len(words) > 3:
                return EntryType.Method
        case ["intrinsic", "function", "reference"]:
            return EntryType.Function

    match words[:2]:
        case ["alexa", "properties"]:
            return EntryType.Property
        case ["alexa", "resource"]:
            return EntryType.Resource
        case ["aws", "attribute"]:
            return EntryType.Attribute
        case ["aws", "properties"]:
            return EntryType.Property
        case ["aws", "resource"]:
            return EntryType.Resource
        case ["transform", "aws"]:
            return EntryType.Macro

    match words[:1]:
        case ["quickref"]:
            return EntryType.Sample

    # fallback to 'Guide'
    return EntryType.Guide


def override_doc_type(metadata: dashify.core.DocMetadata) -> str | None:
    """Hard-coded cases"""
    EntryType = dashify.core.EntryType

    if metadata.title == "AWS::Include transform":
        return EntryType.Macro
    if metadata.title == "AWS::LanguageExtensions transform":
        return EntryType.Macro

    if (
        len(metadata.breadcrumb_url) == 6
        and metadata.breadcrumb_url[3].endswith("/template-guide.html")
        and metadata.breadcrumb_url[4].endswith("/template-anatomy.html")
    ):
        return EntryType.Keyword

    if (
        len(metadata.breadcrumb_url) == 6
        and metadata.breadcrumb_url[3].endswith("/template-reference.html")
        and metadata.breadcrumb_url[4].endswith("/cfn-helper-scripts-reference.html")
    ):
        return EntryType.Command
