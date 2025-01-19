import tomllib
from pathlib import Path

import pytest

from forum_updater import threads

THREAD_CONFIG = """\
first_page_url = "http://somewhere/1234.html"
num_pages = 20
"""


def test_folder_is_thread1(tmp_path: Path):
    assert not threads.folder_is_thread(tmp_path)


def test_folder_is_thread2(tmp_path: Path):
    (tmp_path / "thread.toml").write_text("dummy")
    assert threads.folder_is_thread(tmp_path)


def test_thread_config1(tmp_path: Path):
    # Faulty .toml file
    (tmp_path / "thread.toml").write_text("dummy")
    with pytest.raises(tomllib.TOMLDecodeError):
        threads.thread_config(tmp_path)


def test_thread_config2(tmp_path: Path):
    (tmp_path / "thread.toml").write_text(THREAD_CONFIG)
    config = threads.thread_config(tmp_path)
    assert config.num_pages == 20
