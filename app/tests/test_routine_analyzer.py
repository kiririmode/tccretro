"""RoutineAnalyzerのテスト."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from tccretro.analyzer.routine_analyzer import RoutineAnalyzer


@pytest.fixture
def sample_data_with_routine():
    """ルーチン情報を含むサンプルデータを作成する."""
    return pd.DataFrame(
        {
            "タイムライン日付": ["2025-11-02"] * 5,
            "タスクID": ["task1", "task2", "task3", "task4", "task5"],
            "タスク名": ["タスク1", "タスク2", "タスク3", "タスク4", "タスク5"],
            "プロジェクトID": ["prj1", "prj1", "prj2", "prj2", "prj3"],
            "プロジェクト名": ["プロジェクトA"] * 5,
            "モードID": ["mode1"] * 5,
            "モード名": ["Focus"] * 5,
            "ルーチンID": ["rtn1", "rtn2", "", None, "rtn3"],  # ルーチンと非ルーチンが混在
            "ルーチン名": ["ルーチン1", "ルーチン2", "", "", "ルーチン3"],
            "実績時間": ["01:00:00", "00:30:00", "00:45:00", "00:15:00", "02:00:00"],
        }
    )


@pytest.fixture
def sample_data_all_routine():
    """すべてルーチンタスクのサンプルデータを作成する."""
    return pd.DataFrame(
        {
            "タイムライン日付": ["2025-11-02"] * 3,
            "タスクID": ["task1", "task2", "task3"],
            "タスク名": ["タスク1", "タスク2", "タスク3"],
            "プロジェクトID": ["prj1"] * 3,
            "プロジェクト名": ["プロジェクトA"] * 3,
            "モードID": ["mode1"] * 3,
            "モード名": ["Focus"] * 3,
            "ルーチンID": ["rtn1", "rtn2", "rtn3"],
            "ルーチン名": ["ルーチン1", "ルーチン2", "ルーチン3"],
            "実績時間": ["01:00:00", "00:30:00", "00:30:00"],
        }
    )


@pytest.fixture
def sample_data_no_routine():
    """すべて非ルーチンタスクのサンプルデータを作成する."""
    return pd.DataFrame(
        {
            "タイムライン日付": ["2025-11-02"] * 3,
            "タスクID": ["task1", "task2", "task3"],
            "タスク名": ["タスク1", "タスク2", "タスク3"],
            "プロジェクトID": ["prj1"] * 3,
            "プロジェクト名": ["プロジェクトA"] * 3,
            "モードID": ["mode1"] * 3,
            "モード名": ["Focus"] * 3,
            "ルーチンID": ["", None, ""],
            "ルーチン名": ["", "", ""],
            "実績時間": ["01:00:00", "00:30:00", "00:30:00"],
        }
    )


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリを作成する."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestRoutineAnalyzer:
    """RoutineAnalyzerのテスト."""

    def test_ルーチン別分析が正常に動作する(self, sample_data_with_routine, temp_output_dir):
        """ルーチン別分析が正常に動作することを確認."""
        analyzer = RoutineAnalyzer(sample_data_with_routine, temp_output_dir)
        result = analyzer.analyze()

        assert result.title == "ルーチン別時間分析"
        assert result.summary["total_hours"] == 4.5  # 合計4.5時間
        assert result.chart_path is not None
        assert result.chart_path.exists()
        assert "ルーチン別時間分析" in result.report_section

    def test_ルーチンと非ルーチンの時間集計が正しい(
        self, sample_data_with_routine, temp_output_dir
    ):
        """ルーチンと非ルーチンの時間集計が正しいことを確認."""
        analyzer = RoutineAnalyzer(sample_data_with_routine, temp_output_dir)
        result = analyzer.analyze()

        # ルーチンタスク: task1(1h) + task2(0.5h) + task5(2h) = 3.5時間
        assert result.summary["routine_hours"] == 3.5
        # 非ルーチンタスク: task3(0.75h) + task4(0.25h) = 1時間
        assert result.summary["non_routine_hours"] == 1.0
        # 割合: ルーチン 77.8%, 非ルーチン 22.2%
        assert abs(result.summary["routine_percentage"] - 77.8) < 0.1
        assert abs(result.summary["non_routine_percentage"] - 22.2) < 0.1

    def test_すべてルーチンタスクの場合(self, sample_data_all_routine, temp_output_dir):
        """すべてルーチンタスクの場合の処理を確認."""
        analyzer = RoutineAnalyzer(sample_data_all_routine, temp_output_dir)
        result = analyzer.analyze()

        assert result.summary["routine_hours"] == 2.0  # 合計2時間
        assert result.summary["non_routine_hours"] == 0.0
        assert result.summary["routine_percentage"] == 100.0
        assert result.summary["non_routine_percentage"] == 0.0

    def test_すべて非ルーチンタスクの場合(self, sample_data_no_routine, temp_output_dir):
        """すべて非ルーチンタスクの場合の処理を確認."""
        analyzer = RoutineAnalyzer(sample_data_no_routine, temp_output_dir)
        result = analyzer.analyze()

        assert result.summary["routine_hours"] == 0.0
        assert result.summary["non_routine_hours"] == 2.0  # 合計2時間
        assert result.summary["routine_percentage"] == 0.0
        assert result.summary["non_routine_percentage"] == 100.0

    def test_グラフファイルが生成される(self, sample_data_with_routine, temp_output_dir):
        """グラフファイルが正しいパスに生成されることを確認."""
        analyzer = RoutineAnalyzer(sample_data_with_routine, temp_output_dir)
        result = analyzer.analyze()

        expected_path = temp_output_dir / "charts" / "routine_analysis.png"
        assert result.chart_path == expected_path
        assert result.chart_path.exists()

    def test_レポートセクションに必要な情報が含まれる(
        self, sample_data_with_routine, temp_output_dir
    ):
        """レポートセクションに必要な情報が含まれることを確認."""
        analyzer = RoutineAnalyzer(sample_data_with_routine, temp_output_dir)
        result = analyzer.analyze()

        report = result.report_section
        assert "ルーチン別時間分析" in report
        assert "タスク種別実績時間" in report
        assert "ルーチンタスク" in report
        assert "非ルーチンタスク" in report
        assert "charts/routine_analysis.png" in report
