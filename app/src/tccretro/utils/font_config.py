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

    注意: グラフ内の絵文字は各アナライザーで削除されます。
    """
    system = platform.system()
    font_list = []

    if system == "Darwin":  # macOS
        font_list = ["Hiragino Sans", "Hiragino Maru Gothic Pro"]
    elif system == "Windows":
        font_list = ["Yu Gothic", "MS Gothic", "MS UI Gothic"]
    else:  # Linux
        font_list = ["Noto Sans CJK JP", "IPAexGothic", "IPAGothic", "DejaVu Sans"]

    try:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = font_list
        plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の文字化け対策
        logger.info("日本語フォント設定が完了しました: %s", ", ".join(font_list))
    except Exception as e:
        logger.warning("フォント設定に失敗しました: %s。デフォルトフォントを使用します。", e)
        plt.rcParams["axes.unicode_minus"] = False
