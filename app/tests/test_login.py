"""login.pyモジュールのテスト."""

from unittest.mock import Mock

import pytest

from tccretro.login import TaskChuteLogin, create_login_from_env


class TestTaskChuteLogin:
    """TaskChuteLoginクラスのテストスイート."""

    def test_init(self):
        """__init__: 初期化時に認証情報が正しく設定されることを確認."""
        email = "test@example.com"
        password = "test_password"

        login = TaskChuteLogin(email, password)

        assert login.google_email == email
        assert login.google_password == password
        assert login.base_url == "https://taskchute.cloud"

    def test_login_success_already_logged_in(self, mock_page: Mock):
        """login: すでにログイン済みの場合、Trueを返す."""
        login = TaskChuteLogin("test@example.com", "test_password")

        # ログイン済みURLをモック
        mock_page.url = "https://taskchute.cloud/taskchute"

        result = login.login(mock_page)

        assert result is True
        mock_page.goto.assert_called_once_with("https://taskchute.cloud/taskchute")
        mock_page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    def test_login_failure_not_logged_in(self, mock_page: Mock):
        """login: ログインが必要な場合、Falseを返す."""
        login = TaskChuteLogin("test@example.com", "test_password")

        # ログインページのURLをモック
        mock_page.url = "https://taskchute.cloud/auth/login"
        # ログインボタンが見つかる場合（未ログイン）
        mock_page.wait_for_selector.return_value = True

        result = login.login(mock_page)

        assert result is False

    def test_login_exception_handling(self, mock_page: Mock, capsys):
        """login: 例外が発生した場合、Falseを返しエラーメッセージを表示."""
        login = TaskChuteLogin("test@example.com", "test_password")

        # gotoで例外を発生させる
        mock_page.goto.side_effect = Exception("Network error")

        result = login.login(mock_page)

        assert result is False
        captured = capsys.readouterr()
        assert "エラー: Network error" in captured.out

    def test_is_logged_in_taskchute_url_without_auth(self, mock_page: Mock):
        """_is_logged_in: /taskchute URLで /auth/ がない場合、ログイン済みと判定."""
        login = TaskChuteLogin("test@example.com", "test_password")
        mock_page.url = "https://taskchute.cloud/taskchute"

        result = login._is_logged_in(mock_page)

        assert result is True

    def test_is_logged_in_auth_url(self, mock_page: Mock):
        """_is_logged_in: /auth/ を含むURLの場合、ログインボタンの有無で判定."""
        login = TaskChuteLogin("test@example.com", "test_password")
        mock_page.url = "https://taskchute.cloud/auth/login"

        # ログインボタンが見つかる場合（未ログイン）
        mock_page.wait_for_selector.return_value = True

        result = login._is_logged_in(mock_page)

        assert result is False
        mock_page.wait_for_selector.assert_called_once()

    def test_is_logged_in_no_login_button(self, mock_page: Mock):
        """_is_logged_in: ログインボタンが見つからない場合、ログイン済みと判定."""
        login = TaskChuteLogin("test@example.com", "test_password")
        mock_page.url = "https://taskchute.cloud/some-page"

        # ログインボタンが見つからない（タイムアウト）
        mock_page.wait_for_selector.side_effect = Exception("Timeout")

        result = login._is_logged_in(mock_page)

        assert result is True


class TestCreateLoginFromEnv:
    """create_login_from_env関数のテストスイート."""

    def test_create_from_new_env_vars(self, mock_env: dict[str, str]):
        """create_login_from_env: 新しい環境変数から正しく作成."""
        login = create_login_from_env()

        assert login.google_email == "test@example.com"
        assert login.google_password == "test_password"

    def test_create_from_legacy_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        """create_login_from_env: 古い環境変数からフォールバック."""
        monkeypatch.setenv("TASKCHUTE_USERNAME", "legacy@example.com")
        monkeypatch.setenv("TASKCHUTE_PASSWORD", "legacy_password")

        login = create_login_from_env()

        assert login.google_email == "legacy@example.com"
        assert login.google_password == "legacy_password"

    def test_create_with_new_overrides_legacy(self, monkeypatch: pytest.MonkeyPatch):
        """create_login_from_env: 新しい環境変数が古い環境変数より優先される."""
        monkeypatch.setenv("TASKCHUTE_GOOGLE_EMAIL", "new@example.com")
        monkeypatch.setenv("TASKCHUTE_GOOGLE_PASSWORD", "new_password")
        monkeypatch.setenv("TASKCHUTE_USERNAME", "legacy@example.com")
        monkeypatch.setenv("TASKCHUTE_PASSWORD", "legacy_password")

        login = create_login_from_env()

        assert login.google_email == "new@example.com"
        assert login.google_password == "new_password"

    def test_create_with_no_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        """create_login_from_env: 環境変数がない場合、デフォルト値を使用."""
        # すべての関連環境変数を削除
        for key in [
            "TASKCHUTE_GOOGLE_EMAIL",
            "TASKCHUTE_GOOGLE_PASSWORD",
            "TASKCHUTE_USERNAME",
            "TASKCHUTE_PASSWORD",
        ]:
            monkeypatch.delenv(key, raising=False)

        login = create_login_from_env()

        assert login.google_email == "manual-login"
        assert login.google_password == "manual-login"

    def test_create_with_partial_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        """create_login_from_env: 部分的な環境変数の場合、デフォルト値で補完."""
        monkeypatch.setenv("TASKCHUTE_GOOGLE_EMAIL", "partial@example.com")
        monkeypatch.delenv("TASKCHUTE_GOOGLE_PASSWORD", raising=False)
        monkeypatch.delenv("TASKCHUTE_USERNAME", raising=False)
        monkeypatch.delenv("TASKCHUTE_PASSWORD", raising=False)

        login = create_login_from_env()

        assert login.google_email == "partial@example.com"
        assert login.google_password == "manual-login"
