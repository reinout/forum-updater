import logging
import sys
from pathlib import Path

import typer

from forum_updater import posts, sites, threads

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def download(folder: Path, verbose: bool = False):
    level = verbose and logging.DEBUG or logging.INFO
    logging.basicConfig(level=level)
    if sites.folder_is_site(folder):
        logger.warning("Specify a subfolder (=thread) for an actual download.")
        sites.debug_info(folder)
    elif threads.folder_is_thread(folder):
        threads.download(folder)
        posts.download(folder)
    else:
        sys.exit("No site or thread folder found")


@app.command()
def update(folder: Path, verbose: bool = False):
    level = verbose and logging.DEBUG or logging.INFO
    logging.basicConfig(level=level)
    if sites.folder_is_site(folder):
        logger.warning("Specify a subfolder (=thread) for an actual update action.")
        sites.debug_info(folder)
    elif threads.folder_is_thread(folder):
        posts.update(folder)
    else:
        sys.exit("No site or thread folder found")


if __name__ == "__main__":
    app()
