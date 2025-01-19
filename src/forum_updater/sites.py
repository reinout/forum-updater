import logging
import os
import tomllib
from enum import Enum
from pathlib import Path

import requests
from pydantic import BaseModel

CONFIG_FILENAME = "site.toml"
USER_AGENT = "Personal abload-fixer github.com/reinout/forum-updater"
USER_AGENT_HEADER = {"User-agent": USER_AGENT}

logger = logging.getLogger(__name__)


class SiteTypeEnum(str, Enum):
    stummi = "stummi"


class Site(BaseModel):
    site_type: SiteTypeEnum = SiteTypeEnum.stummi
    base_url: str
    username: str
    # Above: from config file. Below: filled in based on folder name.
    name: str | None = None
    password: str | None = None


def folder_is_site(folder: Path) -> bool:
    config_file = folder / CONFIG_FILENAME
    return config_file.exists()


def site_config(folder: Path) -> Site:
    """Return Site based on site config file in folder"""
    config_file = folder / CONFIG_FILENAME
    config = tomllib.loads(config_file.read_text())
    site = Site.model_validate(config)
    site.name = folder.name
    password_env_var = f"{site.name.upper()}_PASSWORD"
    site.password = os.environ.get(password_env_var)
    if not site.password:
        logger.warning(f"No env var {password_env_var} found.")
    return site


def login(site: Site) -> requests.Session:
    """Log in and return session."""
    if site.site_type == SiteTypeEnum.stummi:
        logger.info("Logging in to stummiforum...")
        form = {"name": site.username, "pww": site.password, "B1": "Login"}
        session = requests.Session()
        response = session.post(
            "https://www.stummiforum.de/login.php", data=form, headers=USER_AGENT_HEADER
        )
        response.raise_for_status()
        return session
    raise RuntimeError(f"Login for site type {site.site_type} not implemented")


def debug_info(folder: Path):
    logger.info("Doing some basic setup tests on the site...")
    site = site_config(folder)
    logger.info(site.model_dump_json())
    homepage = requests.get(site.base_url, headers=USER_AGENT_HEADER)
    homepage.raise_for_status()
    logger.info(f"Homepage status code: {homepage.status_code}")
    session = login(site)
    homepage = session.get(site.base_url, headers=USER_AGENT_HEADER)
    homepage.raise_for_status()
    # logger.info("Homepage content after logging in:")
    # print(homepage.content)
