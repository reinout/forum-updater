import tomllib
from pathlib import Path

import pytest

from forum_updater import sites

SITE_CONFIG = """\
base_url = "https://www.stummiforum.de/"
username = "my-username"
"""


def test_folder_is_site1(tmp_path: Path):
    assert not sites.folder_is_site(tmp_path)


def test_folder_is_site2(tmp_path: Path):
    (tmp_path / "site.toml").write_text("dummy")
    assert sites.folder_is_site(tmp_path)


def test_site_config1(tmp_path: Path):
    # Faulty .toml file
    (tmp_path / "site.toml").write_text("dummy")
    with pytest.raises(tomllib.TOMLDecodeError):
        sites.site_config(tmp_path)


def test_site_config2(tmp_path: Path):
    (tmp_path / "site.toml").write_text(SITE_CONFIG)
    config = sites.site_config(tmp_path)
    assert config.username == "my-username"


def test_site_config3(tmp_path: Path):
    folder = tmp_path / "bruno"
    folder.mkdir()
    (folder / "site.toml").write_text(SITE_CONFIG)
    config = sites.site_config(folder)
    assert config.name == "bruno"
