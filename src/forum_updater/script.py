from pathlib import Path
import typer
import logging
import sys
from forum_updater import sites
from forum_updater import threads


app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def download(folder: Path):
    if sites.folder_is_site(folder):
        logger.warning("Specify a subfolder (=thread) for an actual download.")
        sites.debug_info(folder)
    elif threads.folder_is_thread(folder):
        threads.download(folder)
    else:
        sys.exit("No site or thread folder found")


@app.command()
def update(folder:Path):
    print("Not yet implemented")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app()
