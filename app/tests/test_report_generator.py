"""ReportGeneratorモジュールのテスト."""

import tempfile
from pathlib import Path

import pytest

from tccretro.report_generator import ReportGenerator


@pytest.fixture
def sample_csv_file():
    """テスト用のサンプルCSVファイルを作成する."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(
            "タイムライン日付,タスクID,タスク名,プロジェクトID,プロジェクト名,モードID,モード名,実績時間\n"
        )
        f.write("2025-10-19,task1,タスク1,prj1,プロジェクトA,mode1,Focus,01:00:00\n")
        f.write("2025-10-19,task2,タスク2,prj1,プロジェクトA,mode1,Focus,00:30:00\n")
        f.write("2025-10-19,task3,タスク3,prj2,プロジェクトB,mode2,Living,00:45:00\n")
        csv_path = Path(f.name)

    yield csv_path

    # クリーンアップ
    csv_path.unlink()


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリを作成する."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestReportGenerator:
    """ReportGeneratorのテスト."""

    def test_レポート生成が正常に動作する_AI無効(self, sample_csv_file, temp_output_dir):
        """AI分析を無効にしてレポート生成が正常に動作することを確認."""
        generator = ReportGenerator(
            csv_path=sample_csv_file,
            output_dir=temp_output_dir,
            enable_ai=False,
        )

        report_path = generator.generate_report()

        assert report_path.exists()
        assert report_path.suffix == ".md"

        # レポート内容を確認
        content = report_path.read_text(encoding="utf-8")
        assert "TaskChute Cloud データ分析レポート" in content
        assert "プロジェクト別時間分析" in content
        assert "モード別時間分析" in content

    def test_アナライザーが正しく登録される(self, sample_csv_file, temp_output_dir):
        """アナライザーが正しく登録されることを確認."""
        generator = ReportGenerator(
            csv_path=sample_csv_file,
            output_dir=temp_output_dir,
            enable_ai=False,
        )

        assert len(generator.analyzers) == 2
        assert any(a.name == "project" for a in generator.analyzers)
        assert any(a.name == "mode" for a in generator.analyzers)

    def test_グラフディレクトリが作成される(self, sample_csv_file, temp_output_dir):
        """グラフ保存用ディレクトリが作成されることを確認."""
        generator = ReportGenerator(
            csv_path=sample_csv_file,
            output_dir=temp_output_dir,
            enable_ai=False,
        )

        generator.generate_report()

        charts_dir = temp_output_dir / "charts"
        assert charts_dir.exists()
        assert (charts_dir / "project_analysis.png").exists()
        assert (charts_dir / "mode_analysis.png").exists()
