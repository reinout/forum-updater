import json
import logging
import tomllib
from pathlib import Path

from bs4 import BeautifulSoup
from pydantic import BaseModel

from forum_updater import sites
from forum_updater.utils import USER_AGENT_HEADER

CONFIG_FILENAME = "thread.toml"

logger = logging.getLogger(__name__)


class Thread(BaseModel):
    first_page_url: str
    num_pages: int
    thread_id: str = ""


def folder_is_thread(folder: Path) -> bool:
    config_file = folder / CONFIG_FILENAME
    return config_file.exists()


def thread_config(folder: Path) -> Thread:
    """Return Thread based on thread config file in folder"""
    config_file = folder / CONFIG_FILENAME
    logger.debug(f"Reading {config_file}...")
    config = tomllib.loads(config_file.read_text())
    result = Thread.model_validate(config)
    # Calculate thread id before returning the result
    page_part = result.first_page_url.split("/")[-1]
    # t134944f64-RE-text.html
    id = page_part.split("-")[0]
    id = id.lstrip("t")
    result.thread_id = id
    return result


def page_urls(site: sites.Site, thread: Thread) -> list[str]:
    assert site.site_type == sites.SiteTypeEnum.stummi
    result = []
    # https://www.stummiforum.de/t134944f64-RE-Eifelburgenbahn-eingleisige-Nebenbahn-in.html
    # https://www.stummiforum.de/t134944f64-RE-Eifelburgenbahn-eingleisige-Nebenbahn-in-1.html
    # https://www.stummiforum.de/t134944f64-RE-Eifelburgenbahn-eingleisige-Nebenbahn-in-2.html
    for i in range(thread.num_pages):
        if i == 0:
            result.append(thread.first_page_url)
            continue
        replacement = f"-{i}.html"
        result.append(thread.first_page_url.replace(".html", replacement))
    return result


def download(folder: Path):
    site = sites.site_config(folder.parent)
    thread = thread_config(folder)
    pages_folder = folder / "pages"
    pages_folder.mkdir(exist_ok=True)
    session = sites.login(site)

    for page_number, page_url in enumerate(
        page_urls(site=site, thread=thread), start=1
    ):
        output_file = pages_folder / f"{page_number:03d}.json"
        if output_file.exists():
            logger.debug(
                f"Ignoring page {page_number}, file already exists: {output_file}"
            )
            continue
        output = []
        logger.info(f"Looking at page {page_number}: {page_url}")
        page = session.get(page_url, headers=USER_AGENT_HEADER)
        page.raise_for_status()
        content = BeautifulSoup(page.content, features="html.parser")
        # <div class="post bg1" id="p1513990">
        posts = content.find_all(name="div", class_="post")
        for post in posts:
            post_id = post["id"]
            post_id = post_id.lstrip("p")
            title_line = post.find("h3")
            title = title_line.find("a").string
            author_line = post.find("p", class_="author")
            for a in author_line.find_all("a"):
                if a.string == site.username:
                    logger.debug(
                        f"Found post {post_id} ({title}) by {site.username} on page {page_number}"
                    )
                    output.append({"post_id": post_id, "title": title})
        output_file.write_text(json.dumps(output, indent=2))
        logger.info(f"Wrote {output_file}")
