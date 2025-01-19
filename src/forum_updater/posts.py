import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup

from forum_updater import sites, threads
from forum_updater.utils import USER_AGENT_HEADER

logger = logging.getLogger(__name__)


def download(folder: Path):
    site = sites.site_config(folder.parent)
    thread = threads.thread_config(folder)
    pages_folder = folder / "pages"
    posts_folder = folder / "posts"
    posts_folder.mkdir(exist_ok=True)
    session = sites.login(site)

    page_files = sorted(pages_folder.glob("*.json"))
    post_ids = []
    for page_file in page_files:
        post_ids += json.loads(page_file.read_text())
    logger.info(f"Found {len(post_ids)} posts")

    for post_number, post_id in enumerate(post_ids, start=1):
        output_file = posts_folder / f"{post_number:04d}.txt"
        if output_file.exists():
            logger.debug(
                f"Ignoring post {post_number}, file already exists: {output_file}"
            )
            continue
        edit_url = f"https://www.stummiforum.de/msg.php?Thread={thread.thread_id}&msg={post_id}"
        edit_page = session.get(edit_url, headers=USER_AGENT_HEADER)
        edit_page.raise_for_status()
        content = BeautifulSoup(edit_page.content, features="html.parser")
        # title_tag = content.find("input", id="messagetitle")
        # title = title_tag.attrs["value"])
        text_area = content.find("textarea", id="nachricht")
        text = text_area.string
        output_file.write_text(text)
        logger.info(f"Wrote {output_file}")
