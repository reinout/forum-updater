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
    posts = []
    for page_file in page_files:
        posts += json.loads(page_file.read_text())
    logger.info(f"Found {len(posts)} posts")

    for post_number, post_data in enumerate(posts, start=1):
        post_id = post_data["post_id"]
        # title = post_data["title"]
        output_file = posts_folder / f"{post_number:04d}.txt"
        if output_file.exists():
            logger.debug(
                f"Ignoring post {post_number}, file already exists: {output_file}"
            )
            continue
        edit_url = f"https://www.stummiforum.de/msg.php?Thread={thread.thread_id}&msg={post_id}"
        edit_page = session.get(edit_url, headers=USER_AGENT_HEADER)
        edit_page.raise_for_status()
        content = BeautifulSoup(edit_page.text, features="html.parser")

        # title_tag = content.find("input", id="messagetitle")
        # title = title_tag.attrs["value"])
        text_area = content.find("textarea", id="nachricht")
        if text_area is None:
            logger.warning(f"No textarea found for post={post_id}")
        text = text_area.string
        output_file.write_text(text)
        logger.info(f"Wrote {output_file}")


def update(folder: Path):
    site = sites.site_config(folder.parent)
    thread = threads.thread_config(folder)
    pages_folder = folder / "pages"
    posts_folder = folder / "posts"
    session = sites.login(site)

    page_files = sorted(pages_folder.glob("*.json"))
    posts = []
    for page_file in page_files:
        posts += json.loads(page_file.read_text())
    logger.info(f"Found {len(posts)} posts")

    for post_number, post_data in enumerate(posts, start=1):
        post_id = post_data["post_id"]
        # title = post_data["title"]
        original_file = posts_folder / f"{post_number:04d}.txt"
        assert original_file.exists()
        updated_file = posts_folder / f"{post_number:04d}.txt-updated"
        if not updated_file.exists():
            logger.debug(f"No updated file {updated_file} found, skipping.")
            continue
        new_text = updated_file.read_text()

        actual_thread_id, forum_id = thread.thread_id.split("f")

        edit_url = f"https://www.stummiforum.de/msg.php?forum={forum_id}&Thread={actual_thread_id}&msg={post_id}"

        edit_page = session.get(edit_url, headers=USER_AGENT_HEADER)
        edit_page.raise_for_status()
        encoding = edit_page.encoding
        content = BeautifulSoup(edit_page.text, features="html.parser")

        form = content.find("form", {"name": "newms"})
        form_action = form.attrs["action"]

        title_tag = content.find("input", id="messagetitle")
        title = title_tag.attrs["value"]
        unique_field = content.find("input", {"name": "unique"})
        unique = unique_field.attrs["value"]

        form = {
            "titel": title.encode(encoding),
            "nachricht": new_text.encode(encoding),
            "Submit": "speichern",
            "unique": unique,
        }
        post_url = f"{site.base_url}/{form_action}"
        form_response = session.post(post_url, headers=USER_AGENT_HEADER, data=form)
        form_response.raise_for_status()
        logger.info(f"Posted new content for {edit_url}")
        original_file.unlink()
        updated_file.unlink()
        logger.info(f"Removed {original_file} and the update: re-download everything")
