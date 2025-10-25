"""Analyzerモジュールのテスト."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from tccretro.analyzer.mode_analyzer import ModeAnalyzer
from tccretro.analyzer.project_analyzer import ProjectAnalyzer


@pytest.fixture
def sample_data():
    """テスト用のサンプルデータを作成する."""
    return pd.DataFrame(
        {
            "タイムライン日付": ["2025-10-19"] * 5,
            "タスクID": ["task1", "task2", "task3", "task4", "task5"],
            "タスク名": ["タスク1", "タスク2", "タスク3", "タスク4", "タスク5"],
            "プロジェクトID": ["prj1", "prj1", "prj2", "prj2", "prj3"],
            "プロジェクト名": [
                "プロジェクトA",
                "プロジェクトA",
                "プロジェクトB",
                "プロジェクトB",
                "プロジェクトC",
            ],
            "モードID": ["mode1", "mode1", "mode2", "mode2", "mode1"],
            "モード名": ["Focus", "Focus", "Living", "Living", "Focus"],
            "実績時間": ["01:00:00", "00:30:00", "00:45:00", "00:15:00", "02:00:00"],
        }
    )


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリを作成する."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestProjectAnalyzer:
    """ProjectAnalyzerのテスト."""

    def test_プロジェクト別分析が正常に動作する(self, sample_data, temp_output_dir):
        """プロジェクト別分析が正常に動作することを確認."""
        analyzer = ProjectAnalyzer(sample_data, temp_output_dir)
        result = analyzer.analyze()

        assert result.title == "プロジェクト別時間分析"
        assert result.summary["total_projects"] == 3
        assert result.summary["top_project"] == "プロジェクトC"  # 2時間が最長
        assert result.chart_path is not None
        assert result.chart_path.exists()
        assert "プロジェクト別時間分析" in result.report_section

    def test_プロジェクト別の時間集計が正しい(self, sample_data, temp_output_dir):
        """プロジェクト別の時間集計が正しいことを確認."""
        analyzer = ProjectAnalyzer(sample_data, temp_output_dir)
        result = analyzer.analyze()

        # プロジェクトAは1時間+30分=1.5時間
        assert result.summary["projects"]["プロジェクトA"] == 1.5
        # プロジェクトBは45分+15分=1時間
        assert result.summary["projects"]["プロジェクトB"] == 1.0
        # プロジェクトCは2時間
        assert result.summary["projects"]["プロジェクトC"] == 2.0


class TestModeAnalyzer:
    """ModeAnalyzerのテスト."""

    def test_モード別分析が正常に動作する(self, sample_data, temp_output_dir):
        """モード別分析が正常に動作することを確認."""
        analyzer = ModeAnalyzer(sample_data, temp_output_dir)
        result = analyzer.analyze()

        assert result.title == "モード別時間分析"
        assert result.summary["total_modes"] == 2
        assert result.summary["top_mode"] == "Focus"  # 3.5時間
        assert result.chart_path is not None
        assert result.chart_path.exists()
        assert "モード別時間分析" in result.report_section

    def test_モード別の時間集計が正しい(self, sample_data, temp_output_dir):
        """モード別の時間集計が正しいことを確認."""
        analyzer = ModeAnalyzer(sample_data, temp_output_dir)
        result = analyzer.analyze()

        # Focusは1時間+30分+2時間=3.5時間
        assert result.summary["modes"]["Focus"] == 3.5
        # Livingは45分+15分=1時間
        assert result.summary["modes"]["Living"] == 1.0
