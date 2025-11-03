"""Markdownレポート生成モジュール."""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from tccretro.ai_feedback import AIFeedbackGenerator
from tccretro.analyzer.base import AnalysisResult, IAnalyzer
from tccretro.analyzer.mode_analyzer import ModeAnalyzer
from tccretro.analyzer.project_analyzer import ProjectAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """分析結果を統合してMarkdownレポートを生成するクラス."""

    def __init__(
        self,
        csv_path: Path,
        output_dir: Path,
        enable_ai: bool = True,
        model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    ):
        """ReportGeneratorを初期化する.

        Args:
            csv_path: 分析対象のCSVファイルパス
            output_dir: レポート出力先ディレクトリ
            enable_ai: AI分析を有効にするかどうか
            model_id: 使用するBedrockのモデルIDまたは推論プロファイルID
        """
        self.csv_path = csv_path
        self.output_dir = output_dir
        self.enable_ai = enable_ai
        self.model_id = model_id
        self.data = pd.read_csv(csv_path)
        self.analyzers: list[IAnalyzer] = []

        # アナライザーを登録
        self._register_analyzers()

    def _register_analyzers(self) -> None:
        """利用可能なアナライザーを登録する."""
        self.analyzers = [
            ProjectAnalyzer(self.data, self.output_dir),
            ModeAnalyzer(self.data, self.output_dir),
            # 将来的に他のアナライザーをここに追加
        ]
        logger.info("登録されたアナライザー: %d 個", len(self.analyzers))

    def generate_report(self) -> Path:
        """レポートを生成する.

        Returns:
            Path: 生成されたレポートファイルのパス
        """
        logger.info("レポート生成を開始します")

        # 全アナライザーを実行
        analysis_results: list[AnalysisResult] = []
        for analyzer in self.analyzers:
            analyzer_label = {
                "project": "プロジェクト別分析",
                "mode": "モード別分析",
            }.get(analyzer.name, f"'{analyzer.name}' 分析")

            print(f"  → {analyzer_label}を実行中...")
            logger.info("アナライザー '%s' を実行中...", analyzer.name)
            result = analyzer.analyze()
            analysis_results.append(result)

        # AI分析を実行
        ai_feedback = ""
        if self.enable_ai:
            try:
                print("  → AIフィードバックを生成中... (15-40秒程度かかります)")
                ai_generator = AIFeedbackGenerator(model_id=self.model_id)
                project_result = next(r for r in analysis_results if "プロジェクト" in r.title)
                mode_result = next(r for r in analysis_results if "モード" in r.title)
                ai_feedback = ai_generator.generate_feedback(
                    project_result.summary, mode_result.summary
                )
            except Exception as e:
                logger.warning("AI分析をスキップします: %s", e)
                ai_feedback = "> AI分析は利用できません。AWS認証情報を確認してください。"

        # Markdownレポートを構築
        print("  → レポートを生成中...")
        report_content = self._build_report(analysis_results, ai_feedback)

        # レポートを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"report_{timestamp}.md"
        report_path.write_text(report_content, encoding="utf-8")

        logger.info("レポートを生成しました: %s", report_path)
        return report_path

    def _build_report(self, analysis_results: list[AnalysisResult], ai_feedback: str) -> str:
        """Markdownレポートを構築する.

        Args:
            analysis_results: 各アナライザーの分析結果
            ai_feedback: AI分析のフィードバック

        Returns:
            str: Markdownフォーマットのレポート
        """
        lines = [
            "# TaskChute Cloud データ分析レポート",
            "",
            f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"**分析対象ファイル**: `{self.csv_path.name}`",
            f"**データ行数**: {len(self.data)} タスク",
            "",
            "---",
            "",
        ]

        # 各アナライザーのレポートセクションを追加
        for result in analysis_results:
            lines.append(result.report_section)
            lines.append("")

        # AI分析セクションを追加
        if ai_feedback:
            lines.append("---")
            lines.append("")
            lines.append("# AI分析によるフィードバック")
            lines.append("")
            lines.append(ai_feedback)
            lines.append("")

        # フッター
        lines.extend(
            [
                "---",
                "",
                "*このレポートは tccretro により自動生成されました。*",
                "",
            ]
        )

        return "\n".join(lines)
