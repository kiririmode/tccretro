"""共通テストフィクスチャとユーティリティ."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_page() -> Mock:
    """Playwright Pageオブジェクトのモックを作成します。

    Returns:
        モックされたPageオブジェクト
    """
    page = MagicMock()
    page.url = "https://taskchute.cloud/taskchute"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()
    page.wait_for_selector = MagicMock()
    page.wait_for_timeout = MagicMock()
    page.locator = MagicMock()
    page.click = MagicMock()
    page.fill = MagicMock()
    page.press = MagicMock()
    page.screenshot = MagicMock()
    page.expect_download = MagicMock()
    return page


@pytest.fixture
def mock_locator() -> Mock:
    """Playwright Locatorオブジェクトのモックを作成します。

    Returns:
        モックされたLocatorオブジェクト
    """
    locator = MagicMock()
    locator.count = MagicMock(return_value=1)
    locator.first = locator
    locator.click = MagicMock()
    locator.fill = MagicMock()
    locator.press = MagicMock()
    return locator


@pytest.fixture
def mock_download() -> Mock:
    """Playwright Downloadオブジェクトのモックを作成します。

    Returns:
        モックされたDownloadオブジェクト
    """
    download = MagicMock()
    download.suggested_filename = "test_export.csv"
    download.save_as = MagicMock()
    return download


@pytest.fixture
def temp_download_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """一時的なダウンロードディレクトリを作成します。

    Args:
        tmp_path: pytestのtmp_pathフィクスチャ

    Yields:
        一時ダウンロードディレクトリのパス
    """
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    yield download_dir


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """環境変数のモックを設定します。

    Args:
        monkeypatch: pytestのmonkeypatchフィクスチャ

    Returns:
        設定された環境変数の辞書
    """
    env_vars = {
        "TASKCHUTE_GOOGLE_EMAIL": "test@example.com",
        "TASKCHUTE_GOOGLE_PASSWORD": "test_password",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
