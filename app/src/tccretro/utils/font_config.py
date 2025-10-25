"""日本語フォント設定モジュール.

matplotlibで日本語を正しく表示するための設定を提供します。
"""

import logging
import platform

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def setup_japanese_font() -> None:
    """matplotlibで日本語を表示できるように設定する.

    プラットフォームごとに利用可能な日本語フォントを検出して設定します。
    - macOS: Hiragino Sans
    - Windows: Yu Gothic / MS Gothic
    - Linux: Noto Sans CJK JP / IPAexGothic

    フォントが見つからない場合は警告を出力します。
    """
    system = platform.system()
    font_candidates = []

    if system == "Darwin":  # macOS
        font_candidates = ["Hiragino Sans", "Hiragino Maru Gothic Pro"]
    elif system == "Windows":
        font_candidates = ["Yu Gothic", "MS Gothic", "MS UI Gothic"]
    else:  # Linux
        font_candidates = ["Noto Sans CJK JP", "IPAexGothic", "IPAGothic", "DejaVu Sans"]

    # Try to set font
    for font in font_candidates:
        try:
            plt.rcParams["font.family"] = font
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の文字化け対策
            logger.info("日本語フォント設定が完了しました: %s", font)
            return
        except Exception:
            continue

    # フォールバック: デフォルトフォントを使用
    logger.warning(
        "日本語フォントが見つかりませんでした。デフォルトフォントを使用します。"
        "日本語が文字化けする可能性があります。"
    )
    plt.rcParams["axes.unicode_minus"] = False
