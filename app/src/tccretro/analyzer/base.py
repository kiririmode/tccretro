"""Analyzer base class for extensible data analysis."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class AnalysisResult:
    """分析結果を保持するデータクラス."""

    title: str  # 分析タイトル
    summary: dict[str, Any]  # 集計結果のサマリー
    chart_path: Path | None  # グラフ画像のパス
    report_section: str  # Markdownレポートのセクション


class IAnalyzer(ABC):
    """データ分析を行うアナライザーの抽象基底クラス.

    新しい分析観点を追加する場合は、このクラスを継承して
    analyze() メソッドを実装してください。
    """

    def __init__(self, data: pd.DataFrame, output_dir: Path):
        """アナライザーを初期化する.

        Args:
            data: 分析対象のTaskChute CloudデータのDataFrame
            output_dir: グラフ画像などの出力先ディレクトリ
        """
        self.data = data
        self.output_dir = output_dir
        self.charts_dir = output_dir / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """データを分析して結果を返す.

        Returns:
            AnalysisResult: 分析結果（タイトル、サマリー、グラフ、レポート）
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """アナライザーの名前を返す.

        Returns:
            str: アナライザー名（例: "project", "mode"）
        """
        pass
