from pathlib import Path
from forum_updater import sites


def test_folder_is_site(tmp_path: Path):
    assert sites
