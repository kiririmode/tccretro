"""export.pyモジュールのテスト."""

from contextlib import contextmanager
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from tccretro.export import TaskChuteExporter


class TestTaskChuteExporter:
    """TaskChuteExporterクラスのテストスイート."""

    def test_init_creates_download_dir(self, tmp_path: Path):
        """__init__: ダウンロードディレクトリが作成されることを確認."""
        download_dir = tmp_path / "test_downloads"

        exporter = TaskChuteExporter(download_dir=str(download_dir), debug=False)

        assert exporter.download_dir == download_dir
        assert download_dir.exists()
        assert exporter.debug is False

    def test_init_with_debug_mode(self, tmp_path: Path):
        """__init__: デバッグモードが正しく設定されることを確認."""
        exporter = TaskChuteExporter(download_dir=str(tmp_path), debug=True)

        assert exporter.debug is True

    def test_fill_date_range_single_input_success(self, mock_page: Mock, mock_locator: Mock):
        """fill_date_range: 単一入力方式で日付範囲を正常に入力."""
        exporter = TaskChuteExporter()
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        # 単一入力フィールドが見つかる場合
        mock_locator.count.return_value = 1
        mock_page.locator.return_value = mock_locator

        result = exporter.fill_date_range(mock_page, start_date, end_date)

        assert result is True
        mock_page.locator.assert_called_once_with('input[placeholder*="YYYY"]')
        mock_locator.click.assert_called_once()
        mock_locator.fill.assert_called_once_with("2025/01/01 - 2025/01/31")
        mock_locator.press.assert_called_once_with("Enter")

    def test_fill_date_range_individual_fields_success(self, mock_page: Mock):
        """fill_date_range: 個別フィールド方式で日付範囲を正常に入力."""
        exporter = TaskChuteExporter()
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 20)

        # 単一入力フィールドが見つからない場合
        mock_single_input = MagicMock()
        mock_single_input.count.return_value = 0

        # 個別フィールドのモック
        mock_year_start = MagicMock()
        mock_year_start.count.return_value = 1
        mock_month_start = MagicMock()
        mock_day_start = MagicMock()
        mock_year_end = MagicMock()
        mock_month_end = MagicMock()
        mock_day_end = MagicMock()

        # locatorの呼び出しごとに異なるモックを返す
        locator_map = {
            'input[placeholder*="YYYY"]': mock_single_input,
            '[aria-label="年"][data-range-position="start"]': mock_year_start,
            '[aria-label="月"][data-range-position="start"]': mock_month_start,
            '[aria-label="日"][data-range-position="start"]': mock_day_start,
            '[aria-label="年"][data-range-position="end"]': mock_year_end,
            '[aria-label="月"][data-range-position="end"]': mock_month_end,
            '[aria-label="日"][data-range-position="end"]': mock_day_end,
        }

        def locator_side_effect(selector: str):
            mock = locator_map.get(selector, MagicMock())
            mock.first = mock
            return mock

        mock_page.locator.side_effect = locator_side_effect

        result = exporter.fill_date_range(mock_page, start_date, end_date)

        assert result is True
        # 各フィールドに正しい値が入力されたことを確認
        mock_year_start.fill.assert_called_once_with("2025")
        mock_month_start.fill.assert_called_once_with("1")
        mock_day_start.fill.assert_called_once_with("15")
        mock_year_end.fill.assert_called_once_with("2025")
        mock_month_end.fill.assert_called_once_with("1")
        mock_day_end.fill.assert_called_once_with("20")

    def test_fill_date_range_failure_no_fields(self, mock_page: Mock):
        """fill_date_range: 日付フィールドが見つからない場合、Falseを返す."""
        exporter = TaskChuteExporter()
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        # すべてのフィールドが見つからない
        mock_locator = MagicMock()
        mock_locator.count.return_value = 0
        mock_page.locator.return_value = mock_locator

        result = exporter.fill_date_range(mock_page, start_date, end_date)

        assert result is False

    def test_fill_date_range_exception_handling(self, mock_page: Mock, capsys):
        """fill_date_range: 例外が発生した場合、Falseを返す."""
        exporter = TaskChuteExporter()
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        # locatorで例外を発生させる
        mock_page.locator.side_effect = Exception("Element not found")

        result = exporter.fill_date_range(mock_page, start_date, end_date)

        assert result is False
        captured = capsys.readouterr()
        assert "日付範囲の入力に失敗しました" in captured.out

    def test_export_data_success(
        self, mock_page: Mock, mock_locator: Mock, mock_download: Mock, temp_download_dir: Path
    ):
        """export_data: データエクスポートが正常に成功."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir), debug=False)
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        # fill_date_rangeをモック化
        with patch.object(exporter, "fill_date_range", return_value=True):
            # ダウンロードボタンのモック
            mock_locator.count.return_value = 1
            mock_page.locator.return_value = mock_locator

            # ダウンロードのモック
            @contextmanager
            def mock_expect_download(timeout):
                yield type("obj", (object,), {"value": mock_download})

            mock_page.expect_download = mock_expect_download

            result = exporter.export_data(mock_page, start_date, end_date)

            assert result is not None
            assert "test_export.csv" in result
            mock_page.goto.assert_called_once_with(
                "https://taskchute.cloud/export/csv-export", timeout=30000
            )
            mock_locator.click.assert_called_once()
            mock_download.save_as.assert_called_once()

    def test_export_data_default_dates(
        self, mock_page: Mock, mock_locator: Mock, mock_download: Mock, temp_download_dir: Path
    ):
        """export_data: 日付が指定されていない場合、デフォルト（昨日）を使用."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir))

        with patch.object(exporter, "fill_date_range", return_value=True) as mock_fill:
            mock_locator.count.return_value = 1
            mock_page.locator.return_value = mock_locator

            @contextmanager
            def mock_expect_download(timeout):
                yield type("obj", (object,), {"value": mock_download})

            mock_page.expect_download = mock_expect_download

            exporter.export_data(mock_page)

            # fill_date_rangeが呼ばれたことを確認（具体的な日付の検証は省略）
            assert mock_fill.called

    def test_export_data_fill_date_failure(self, mock_page: Mock, temp_download_dir: Path):
        """export_data: 日付入力に失敗した場合、Noneを返す."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir))

        with patch.object(exporter, "fill_date_range", return_value=False):
            result = exporter.export_data(mock_page, date(2025, 1, 1), date(2025, 1, 31))

            assert result is None

    def test_export_data_no_download_button(self, mock_page: Mock, temp_download_dir: Path):
        """export_data: ダウンロードボタンが見つからない場合、Noneを返す."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir))

        with patch.object(exporter, "fill_date_range", return_value=True):
            # ダウンロードボタンが見つからない
            mock_locator = MagicMock()
            mock_locator.count.return_value = 0
            mock_page.locator.return_value = mock_locator

            result = exporter.export_data(mock_page, date(2025, 1, 1), date(2025, 1, 31))

            assert result is None

    def test_export_data_with_debug_screenshots(
        self, mock_page: Mock, mock_locator: Mock, mock_download: Mock, temp_download_dir: Path
    ):
        """export_data: デバッグモード時にスクリーンショットが保存される."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir), debug=True)

        with patch.object(exporter, "fill_date_range", return_value=True):
            mock_locator.count.return_value = 1
            mock_page.locator.return_value = mock_locator

            @contextmanager
            def mock_expect_download(timeout):
                yield type("obj", (object,), {"value": mock_download})

            mock_page.expect_download = mock_expect_download

            exporter.export_data(mock_page, date(2025, 1, 1), date(2025, 1, 31))

            # スクリーンショットが複数回呼ばれることを確認
            assert mock_page.screenshot.call_count >= 2

    def test_export_data_exception_handling(self, mock_page: Mock, temp_download_dir: Path, capsys):
        """export_data: 例外が発生した場合、Noneを返す."""
        exporter = TaskChuteExporter(download_dir=str(temp_download_dir))

        # gotoで例外を発生させる
        mock_page.goto.side_effect = Exception("Network error")

        result = exporter.export_data(mock_page, date(2025, 1, 1), date(2025, 1, 31))

        assert result is None
        captured = capsys.readouterr()
        assert "エクスポートがエラーで失敗しました" in captured.out

    def test_wait_for_export_button_success(self, mock_page: Mock):
        """wait_for_export_button: エクスポートボタンが見つかった場合、Trueを返す."""
        exporter = TaskChuteExporter()

        # 最初のセレクタで見つかる
        mock_page.wait_for_selector.return_value = True

        result = exporter.wait_for_export_button(mock_page, timeout=5000)

        assert result is True
        mock_page.wait_for_selector.assert_called_once_with(
            'button:has-text("エクスポート")', timeout=5000
        )

    def test_wait_for_export_button_fallback_selector(self, mock_page: Mock):
        """wait_for_export_button: 複数のセレクタを試行し、見つかった場合Trueを返す."""
        exporter = TaskChuteExporter()

        # 最初のセレクタでは見つからず、2番目で見つかる
        call_count = 0

        def wait_side_effect(selector, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Not found")
            return True

        mock_page.wait_for_selector.side_effect = wait_side_effect

        result = exporter.wait_for_export_button(mock_page)

        assert result is True
        assert mock_page.wait_for_selector.call_count == 2

    def test_wait_for_export_button_not_found(self, mock_page: Mock):
        """wait_for_export_button: すべてのセレクタで見つからない場合、Falseを返す."""
        exporter = TaskChuteExporter()

        # すべてのセレクタで見つからない
        mock_page.wait_for_selector.side_effect = Exception("Not found")

        result = exporter.wait_for_export_button(mock_page)

        assert result is False
        # 4つのセレクタすべてが試行される
        assert mock_page.wait_for_selector.call_count == 4
