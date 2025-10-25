"""モード別の時間分析アナライザー."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from tccretro.analyzer.base import AnalysisResult, IAnalyzer
from tccretro.utils.font_config import setup_japanese_font

logger = logging.getLogger(__name__)


class ModeAnalyzer(IAnalyzer):
    """モードごとの時間集計と可視化を行うアナライザー."""

    @property
    def name(self) -> str:
        """アナライザー名を返す."""
        return "mode"

    def analyze(self) -> AnalysisResult:
        """モードごとの時間集計を分析する.

        Returns:
            AnalysisResult: モード別の集計結果とグラフ
        """
        logger.info("モード別分析を開始します")

        # 実績時間を秒に変換
        self.data["実績時間_秒"] = pd.to_timedelta(self.data["実績時間"]).dt.total_seconds()

        # モードごとに集計
        mode_summary = (
            self.data.groupby("モード名")["実績時間_秒"].sum().sort_values(ascending=False)
        )

        # 時間形式に変換 (HH:MM:SS)
        mode_hours = mode_summary / 3600  # 時間単位

        # グラフ生成
        chart_path = self._generate_charts(mode_summary, mode_hours)

        # レポートセクション生成
        report_section = self._generate_report_section(mode_hours)

        # サマリー作成
        summary = {
            "total_modes": len(mode_summary),
            "total_hours": mode_summary.sum() / 3600,
            "top_mode": mode_summary.idxmax() if not mode_summary.empty else None,
            "top_mode_hours": mode_summary.max() / 3600 if not mode_summary.empty else 0,
            "modes": {name: round(hours, 2) for name, hours in mode_hours.items()},
        }

        logger.info("モード別分析が完了しました: %d モード", len(mode_summary))

        return AnalysisResult(
            title="モード別時間分析",
            summary=summary,
            chart_path=chart_path,
            report_section=report_section,
        )

    def _generate_charts(self, mode_summary: pd.Series, mode_hours: pd.Series) -> Path:
        """モード別のグラフを生成する.

        Args:
            mode_summary: モード別の実績時間（秒）
            mode_hours: モード別の実績時間（時間）

        Returns:
            Path: 生成したグラフ画像のパス
        """
        # 日本語フォント設定
        setup_japanese_font()

        # 絵文字を削除したラベルを作成
        clean_labels = self._remove_emoji(mode_summary.index)

        # 2つのサブプロットを作成
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("モード別時間分析", fontsize=16, fontweight="bold")

        # 1. 円グラフ
        colors = sns.color_palette("Set2", len(mode_summary))
        ax1.pie(
            mode_summary,
            labels=clean_labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        ax1.set_title("モード別時間配分")

        # 2. 棒グラフ
        ax2.barh(clean_labels, mode_hours.values, color=colors)
        ax2.set_xlabel("時間 (h)")
        ax2.set_title("モード別実績時間")
        ax2.invert_yaxis()  # 上位から表示

        plt.tight_layout()

        # 画像保存
        chart_path = self.charts_dir / "mode_analysis.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("モード別グラフを生成しました: %s", chart_path)
        return chart_path

    def _remove_emoji(self, labels: pd.Index) -> list[str]:
        """ラベルから絵文字を削除する.

        Args:
            labels: 元のラベル

        Returns:
            list[str]: 絵文字を削除したラベルのリスト
        """
        import re

        # 絵文字を削除する正規表現パターン
        emoji_pattern = re.compile(
            "["
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f700-\U0001f77f"  # alchemical symbols
            "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
            "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
            "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
            "\U0001fa00-\U0001fa6f"  # Chess Symbols
            "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
            "\U00002600-\U000027bf"  # Miscellaneous Symbols and Dingbats
            "\U0000fe00-\U0000fe0f"  # Variation Selectors
            "]+",
            flags=re.UNICODE,
        )

        return [emoji_pattern.sub("", str(label)).strip() for label in labels]

    def _generate_report_section(self, mode_hours: pd.Series) -> str:
        """レポートのMarkdownセクションを生成する.

        Args:
            mode_hours: モード別の実績時間（時間）

        Returns:
            str: Markdownフォーマットのレポートセクション
        """
        lines = [
            "## モード別時間分析",
            "",
            f"**分析対象モード数**: {len(mode_hours)} モード",
            f"**合計時間**: {mode_hours.sum():.2f} 時間",
            "",
            "### モード別実績時間",
            "",
        ]

        # テーブル形式で表示
        lines.append("| モード名 | 実績時間 (h) | 割合 (%) |")
        lines.append("|---|---:|---:|")

        total_hours = mode_hours.sum()
        for name, hours in mode_hours.items():
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            lines.append(f"| {name} | {hours:.2f} | {percentage:.1f} |")

        lines.append("")
        lines.append("### グラフ")
        lines.append("")
        lines.append("![モード別時間分析](charts/mode_analysis.png)")
        lines.append("")

        return "\n".join(lines)
