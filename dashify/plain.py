from __future__ import annotations

import logging
import urllib.parse
import uuid
from pathlib import Path

import bs4
import click

import dashify.core

logger = logging.getLogger(__name__)


@dashify.core.entry.command()
@click.option(
    "-t",
    "--title",
    default="Test Amazon Docset",
    show_default=True,
    help="Docset title",
)
@click.option(
    "-i",
    "--identifier",
    metavar="IDENTIFIER",
    default=f"aws-{uuid.uuid1()}",
    help="Docset identifier. If not given, a random UUID is used",
)
@click.option(
    "-f",
    "--family",
    metavar="FAMILY",
    default="Test Amazon Docset",
    show_default=True,
    help="Platform family name for the docset",
)
@click.option(
    "-u",
    "--site-url",
    type=dashify.core.URL(),
    required=True,
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
    "-m",
    "--main-page",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the main page of the docset",
)
@click.option(
    "-d",
    "--docset-path",
    metavar="DOCSET",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to output docset",
)
def plain(
    title: str,
    identifier: str,
    family: str,
    site_url: str,
    root_dir: Path,
    main_page: Path,
    docset_path: Path,
):
    """Convert downloaded HTML document to a docset without given the doc type
    in index. This entry point is used for testing purpose."""
    docset_path = dashify.core.prepare_docset(docset_path)
    logger.info(f"Convert docs from '{root_dir}' to '{docset_path}'")

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
        indexes.append(
            {
                "name": metadata.title,
                "type": dashify.core.EntryType.Guide,
                "path": doc_file.name,
            }
        )

    dashify.core.create_docset_index(docset_path, indexes)

    # finalise
    metadata = {
        "CFBundleIdentifier": identifier,
        "CFBundleName": title,
        "DocSetPlatformFamily": family,
        "DashDocSetFallbackURL": site_url,
    }

    if main_page:
        site_base = root_dir / Path(urllib.parse.urlsplit(site_url).path[1:])
        main_page_link = main_page.relative_to(site_base)
        metadata["dashIndexFilePath"] = str(main_page_link)

    dashify.core.create_info_plist(docset_path, metadata)

    # done
    logger.info("Done! Docset created at %s", docset_path)
