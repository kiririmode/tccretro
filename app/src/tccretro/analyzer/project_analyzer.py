"""プロジェクト別の時間分析アナライザー."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from tccretro.analyzer.base import AnalysisResult, IAnalyzer
from tccretro.utils.font_config import setup_japanese_font

logger = logging.getLogger(__name__)


class ProjectAnalyzer(IAnalyzer):
    """プロジェクトごとの時間集計と可視化を行うアナライザー."""

    @property
    def name(self) -> str:
        """アナライザー名を返す."""
        return "project"

    def analyze(self) -> AnalysisResult:
        """プロジェクトごとの時間集計を分析する.

        Returns:
            AnalysisResult: プロジェクト別の集計結果とグラフ
        """
        logger.info("プロジェクト別分析を開始します")

        # 実績時間を秒に変換
        self.data["実績時間_秒"] = pd.to_timedelta(self.data["実績時間"]).dt.total_seconds()

        # プロジェクトごとに集計
        project_summary = (
            self.data.groupby("プロジェクト名")["実績時間_秒"].sum().sort_values(ascending=False)
        )

        # 時間形式に変換 (HH:MM:SS)
        project_hours = project_summary / 3600  # 時間単位

        # グラフ生成
        chart_path = self._generate_charts(project_summary, project_hours)

        # レポートセクション生成
        report_section = self._generate_report_section(project_hours)

        # サマリー作成
        summary = {
            "total_projects": len(project_summary),
            "total_hours": project_summary.sum() / 3600,
            "top_project": project_summary.idxmax() if not project_summary.empty else None,
            "top_project_hours": project_summary.max() / 3600 if not project_summary.empty else 0,
            "projects": {name: round(hours, 2) for name, hours in project_hours.items()},
        }

        logger.info("プロジェクト別分析が完了しました: %d プロジェクト", len(project_summary))

        return AnalysisResult(
            title="プロジェクト別時間分析",
            summary=summary,
            chart_path=chart_path,
            report_section=report_section,
        )

    def _generate_charts(self, project_summary: pd.Series, project_hours: pd.Series) -> Path:
        """プロジェクト別のグラフを生成する.

        Args:
            project_summary: プロジェクト別の実績時間（秒）
            project_hours: プロジェクト別の実績時間（時間）

        Returns:
            Path: 生成したグラフ画像のパス
        """
        # 日本語フォント設定
        setup_japanese_font()

        # 2つのサブプロットを作成
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("プロジェクト別時間分析", fontsize=16, fontweight="bold")

        # 1. 円グラフ
        colors = sns.color_palette("husl", len(project_summary))
        ax1.pie(
            project_summary,
            labels=project_summary.index,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        ax1.set_title("プロジェクト別時間配分")

        # 2. 棒グラフ
        ax2.barh(project_hours.index, project_hours.values, color=colors)
        ax2.set_xlabel("時間 (h)")
        ax2.set_title("プロジェクト別実績時間")
        ax2.invert_yaxis()  # 上位から表示

        plt.tight_layout()

        # 画像保存
        chart_path = self.charts_dir / "project_analysis.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("プロジェクト別グラフを生成しました: %s", chart_path)
        return chart_path

    def _generate_report_section(self, project_hours: pd.Series) -> str:
        """レポートのMarkdownセクションを生成する.

        Args:
            project_hours: プロジェクト別の実績時間（時間）

        Returns:
            str: Markdownフォーマットのレポートセクション
        """
        lines = [
            "## プロジェクト別時間分析",
            "",
            f"**分析対象プロジェクト数**: {len(project_hours)} プロジェクト",
            f"**合計時間**: {project_hours.sum():.2f} 時間",
            "",
            "### プロジェクト別実績時間",
            "",
        ]

        # テーブル形式で表示
        lines.append("| プロジェクト名 | 実績時間 (h) | 割合 (%) |")
        lines.append("|---|---:|---:|")

        total_hours = project_hours.sum()
        for name, hours in project_hours.items():
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            lines.append(f"| {name} | {hours:.2f} | {percentage:.1f} |")

        lines.append("")
        lines.append("### グラフ")
        lines.append("")
        lines.append("![プロジェクト別時間分析](charts/project_analysis.png)")
        lines.append("")

        return "\n".join(lines)
