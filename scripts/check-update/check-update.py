#! /usr/bin/env python3
import datetime
import logging

import click
import feedparser

logger = logging.getLogger("main")


@click.command()
@click.argument("url", envvar="RSS_FEED")
def main(url: str):
    """Script to check for updates of the documentation.

    This script is intended to be run as a GitHub Action.
    """
    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info(f"Checking feed: {url}")

    # parse the feed
    d = feedparser.parse(url)

    # last build time
    feed_update_time = datetime.datetime(
        *d.feed.updated_parsed[:6], tzinfo=datetime.UTC
    )
    logger.info(f"Feed last updated: {feed_update_time}")

    write("last-build-date", feed_update_time.strftime("%Y-%m-%d"))
    write("last-build-time", int(feed_update_time.timestamp()))

    # updated item(s)
    lastest_entry = max(d.entries, key=lambda e: e.updated_parsed)
    lastest_entry_time = datetime.datetime(
        *lastest_entry.updated_parsed[:6], tzinfo=datetime.UTC
    )

    if lastest_entry_time > feed_update_time - datetime.timedelta(days=1):
        logger.info("Related entry found: %s", lastest_entry.title)
        write("entry-title", lastest_entry.title)
        write("entry-link", lastest_entry.link)
        write("entry-updated-time", int(lastest_entry.timestamp()))
        write("entry-summary", lastest_entry.summary)
    else:
        logger.info(f"Most recent entry is too old: {lastest_entry_time}")


def write(key: str, value) -> None:
    value = str(value).strip()
    if "\n" in value:
        setter = f"<<EoM\n{value}\nEoM"
    else:
        setter = f"={value}"
    click.echo(click.style(f"{key}{setter}", fg="white", dim=True))


if __name__ == "__main__":
    main()
