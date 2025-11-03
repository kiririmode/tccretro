"""ルーチン別の時間分析アナライザー."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from tccretro.analyzer.base import AnalysisResult, IAnalyzer
from tccretro.utils.font_config import setup_japanese_font

logger = logging.getLogger(__name__)


class RoutineAnalyzer(IAnalyzer):
    """ルーチンタスクと非ルーチンタスクの時間集計と可視化を行うアナライザー."""

    @property
    def name(self) -> str:
        """アナライザー名を返す."""
        return "routine"

    def analyze(self) -> AnalysisResult:
        """ルーチン vs 非ルーチンの時間集計を分析する.

        Returns:
            AnalysisResult: ルーチン別の集計結果とグラフ
        """
        logger.info("ルーチン別分析を開始します")

        # 実績時間を秒に変換
        self.data["実績時間_秒"] = pd.to_timedelta(self.data["実績時間"]).dt.total_seconds()

        # ルーチンタスクと非ルーチンタスクを分類
        self.data["タスク種別"] = self.data["ルーチンID"].apply(
            lambda x: "ルーチンタスク"
            if pd.notna(x) and str(x).strip() != ""
            else "非ルーチンタスク"
        )

        # タスク種別ごとに集計
        routine_summary = (
            self.data.groupby("タスク種別")["実績時間_秒"].sum().sort_values(ascending=False)
        )

        # 時間形式に変換 (HH:MM:SS)
        routine_hours = routine_summary / 3600  # 時間単位

        # グラフ生成
        chart_path = self._generate_charts(routine_summary, routine_hours)

        # レポートセクション生成
        report_section = self._generate_report_section(routine_hours)

        # サマリー作成
        total_hours = routine_summary.sum() / 3600
        routine_hours_val = routine_summary.get("ルーチンタスク", 0) / 3600
        non_routine_hours_val = routine_summary.get("非ルーチンタスク", 0) / 3600
        routine_percentage = (routine_hours_val / total_hours * 100) if total_hours > 0 else 0

        summary = {
            "total_hours": total_hours,
            "routine_hours": routine_hours_val,
            "non_routine_hours": non_routine_hours_val,
            "routine_percentage": round(routine_percentage, 1),
            "non_routine_percentage": round(100 - routine_percentage, 1),
        }

        logger.info(
            "ルーチン別分析が完了しました: ルーチン %.2f時間 (%.1f%%), 非ルーチン %.2f時間 (%.1f%%)",
            routine_hours_val,
            routine_percentage,
            non_routine_hours_val,
            100 - routine_percentage,
        )

        return AnalysisResult(
            title="ルーチン別時間分析",
            summary=summary,
            chart_path=chart_path,
            report_section=report_section,
        )

    def _generate_charts(self, routine_summary: pd.Series, routine_hours: pd.Series) -> Path:
        """ルーチン別のグラフを生成する.

        Args:
            routine_summary: タスク種別の実績時間（秒）
            routine_hours: タスク種別の実績時間（時間）

        Returns:
            Path: 生成したグラフ画像のパス
        """
        # 日本語フォント設定
        setup_japanese_font()

        # 2つのサブプロットを作成
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("ルーチン別時間分析", fontsize=16, fontweight="bold")

        # 1. 円グラフ
        colors = sns.color_palette("Pastel1", len(routine_summary))
        ax1.pie(
            routine_summary,
            labels=routine_summary.index,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        ax1.set_title("ルーチン vs 非ルーチン時間配分")

        # 2. 棒グラフ
        ax2.bar(routine_summary.index, routine_hours.values, color=colors)
        ax2.set_ylabel("時間 (h)")
        ax2.set_title("タスク種別実績時間")
        ax2.tick_params(axis="x", rotation=0)

        plt.tight_layout()

        # 画像保存
        chart_path = self.charts_dir / "routine_analysis.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("ルーチン別グラフを生成しました: %s", chart_path)
        return chart_path

    def _generate_report_section(self, routine_hours: pd.Series) -> str:
        """レポートのMarkdownセクションを生成する.

        Args:
            routine_hours: タスク種別の実績時間（時間）

        Returns:
            str: Markdownフォーマットのレポートセクション
        """
        lines = [
            "## ルーチン別時間分析",
            "",
            f"**合計時間**: {routine_hours.sum():.2f} 時間",
            "",
            "### タスク種別実績時間",
            "",
        ]

        # テーブル形式で表示
        lines.append("| タスク種別 | 実績時間 (h) | 割合 (%) |")
        lines.append("|---|---:|---:|")

        total_hours = routine_hours.sum()
        for name, hours in routine_hours.items():
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            lines.append(f"| {name} | {hours:.2f} | {percentage:.1f} |")

        lines.append("")
        lines.append("### グラフ")
        lines.append("")
        lines.append("![ルーチン別時間分析](charts/routine_analysis.png)")
        lines.append("")

        return "\n".join(lines)
