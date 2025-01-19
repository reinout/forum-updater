import tomllib
from pathlib import Path

from pydantic import BaseModel

CONFIG_FILENAME = "thread.toml"


class Thread(BaseModel):
    forum_id: str
    num_pages: int


def folder_is_thread(folder: Path) -> bool:
    config_file = folder / CONFIG_FILENAME
    return config_file.exists()


def thread_config(folder: Path) -> Thread:
    """Return Thread based on thread config file in folder"""
    config_file = folder / CONFIG_FILENAME
    config = tomllib.loads(config_file.read_text())
    return Thread.model_validate(config)
