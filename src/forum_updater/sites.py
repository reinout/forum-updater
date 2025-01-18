from pathlib import Path

from pydantic import BaseModel

CONFIG_FILENAME = "site.toml"


class Site(BaseModel):
    name: str
    base_url: str
    username: str


def folder_is_site(folder: Path) -> bool:
    config_file = folder / CONFIG_FILENAME
    return config_file.exists()
