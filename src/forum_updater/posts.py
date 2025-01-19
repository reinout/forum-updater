import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from forum_updater import sites, threads
from forum_updater.utils import USER_AGENT_HEADER

ABLOAD_REGEX = re.compile(
    r"""
    (  # Start of match
    https?             # http/https
    ://abload.de       # domeinnaam
    \S+?               # Non-whitespace characters, non-greedy
    )                  # End of match
    [\[\]]             # Start/end of a tag
    """,
    flags=re.VERBOSE | re.IGNORECASE,
)
NEW_LOCATION = "https://reinout.vanrees.org/abload/"


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

    for post_number, post_id in enumerate(posts, start=1):
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
            "nachricht": new_text.encode(encoding, "xmlcharrefreplace"),
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


def _extract_image(url):
    """Return image, when recognised"""
    url = url.replace("http://abload.de/", "")
    url = url.replace("https://abload.de/", "")
    if url == "index.php":
        return
    if url.startswith("thumb/") or url.startswith("img/"):
        return url.split("/")[1]
    if url.startswith("image.php?img="):
        return url.split("=")[1]
    return


def fix_abload(folder: Path):
    posts_folder = folder / "posts"
    assert posts_folder.exists()

    post_files = sorted(posts_folder.glob("*.txt"))
    for post_file in post_files:
        logger.debug(f"Looking at {post_file}...")
        original_contents = post_file.read_text()
        new_contents = original_contents
        matches = ABLOAD_REGEX.findall(original_contents)
        for url in matches:
            image = _extract_image(url)
            if not image:
                logger.warning(f"Unrecognised url: {url}")
                continue
            new_url = NEW_LOCATION + image
            new_contents = new_contents.replace(url, new_url)
            logger.debug(f"Replaced {url} with {new_url}")
        if original_contents != new_contents:
            new_file = post_file.parent / (post_file.name + "-updated")
            new_file.write_text(new_contents)
            logger.info(f"Wrote {new_file}")
