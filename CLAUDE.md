# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

TaskChute Cloud Retrospective Analysis Tool: Playwrightブラウザ自動化を使用してTaskChute Cloudのデータをローカルに自動エクスポートし、pandasによる分析・可視化、さらにBedrock (Claude) による洞察を得ることで、より良い暮らしのための時間の使い方に関するフィードバックを提供するツール。

**主要機能:**

1. **データエクスポート**: TaskChute Cloudから時間記録データを自動取得
2. **データ分析**: pandasを使った統計分析・可視化
3. **AIフィードバック**: Amazon Bedrock (Claude) によるデータ分析と改善提案

**アーキテクチャフロー:**
CLI実行 → Playwright (永続的Chromeプロファイル) → TaskChute Cloud (ログイン確認 + エクスポート) → ローカルファイル → pandas分析 → Bedrock (Claude) → フィードバック生成

## 技術スタック

- **Python 3.10+** - **uv** (パッケージマネージャ)で管理
- **Playwright** - ブラウザ自動化 (Chromium)
- **永続的Chromeプロファイル** - 認証情報の保存
- **pandas** - データ分析・可視化
- **jpholiday** - 日本の祝日判定
- **Amazon Bedrock (Claude)** - AI分析とフィードバック生成

## 主要コマンド

### 開発環境セットアップ

```bash
# 依存関係のインストール (appディレクトリから)
cd app
uv sync

# Playwrightブラウザのインストール
uv run playwright install chromium

# pre-commitフックのインストール (オプション)
uv run pre-commit install
```

### コード品質

```bash
# すべてのlinter/formatterを実行
uv run pre-commit run --all-files

# Python固有
uv run ruff format app/              # コードフォーマット
uv run ruff check app/ --fix         # 自動修正付きlint
uv run mypy app/src/                 # 型チェック
```

### テスト

```bash
# テスト実行
cd app
uv run pytest tests/ -v

# カバレッジ付きテスト実行
uv run pytest tests/ --cov=src/tccretro --cov-report=term

# HTMLカバレッジレポート生成
uv run pytest tests/ --cov=src/tccretro --cov-report=html
# ブラウザでhtmlcov/index.htmlを開く
```

**テスト方針:**

- **カバレッジ目標: 85%以上** - 主要ロジックは必ずテストでカバーする
- **DRY原則を厳守** - 共通フィクスチャとヘルパーメソッドで重複を徹底的に排除
- **わかりやすさ重視** - 各テストケースには日本語のdocstringを記述
- **テスト構成:**
  - `app/tests/conftest.py` - 共通フィクスチャ (mock_page, mock_locatorなど)
  - `app/tests/test_login.py` - login.pyのテスト
  - `app/tests/test_export.py` - export.pyのテスト
  - `app/tests/test_cli.py` - cli.pyのテスト
  - `app/tests/test_ai_feedback.py` - ai_feedback.pyのテスト（CSV抽出、休日判定など）
  - `app/tests/test_report_generator.py` - report_generator.pyのテスト
  - `app/tests/test_analyzer.py` - アナライザーのテスト
  - `app/tests/test_routine_analyzer.py` - ルーチンアナライザーのテスト

**テスト作成時の注意点:**

- Playwrightオブジェクトは必ずモック化する
- CLIテストでは`runner.isolated_filesystem()`を使用
- 正常系・異常系・エッジケースをすべてカバー
- 重複するモック設定はヘルパーメソッドに抽出

### ローカル実行

```bash
# CLIツールを使用 (推奨)
cd app

# 初回: ログイン認証の保存
uv run python -m tccretro.cli --login-only --debug

# 基本実行 (昨日のデータをエクスポート)
uv run python -m tccretro.cli

# エクスポート + データ分析 + AIフィードバック生成
uv run python -m tccretro.cli --analyze

# エクスポート + データ分析のみ (AI分析なし)
uv run python -m tccretro.cli --analyze --no-ai

# 特定の日付をエクスポート
uv run python -m tccretro.cli --export-date 2025-01-15

# 日付範囲を指定して分析
uv run python -m tccretro.cli --export-start-date 2025-01-01 --export-end-date 2025-01-31 --analyze

# デバッグモード (ブラウザを表示)
uv run python -m tccretro.cli --debug

# スローモーション実行
uv run python -m tccretro.cli --slow-mo 1000 --debug

# 保存先を指定
uv run python -m tccretro.cli --output-dir ./my_exports
```

## プロジェクトアーキテクチャ

### ディレクトリ構造

```text
app/                         # Pythonアプリケーション
├── src/tccretro/           # メインパッケージ
│   ├── analyzer/           # データ分析モジュール
│   │   ├── base.py         # アナライザー基底クラス
│   │   ├── project_analyzer.py  # プロジェクト別分析
│   │   └── mode_analyzer.py     # モード別分析
│   ├── utils/              # ユーティリティ
│   │   └── font_config.py  # 日本語フォント設定
│   ├── login.py            # Playwrightログイン状態確認
│   ├── export.py           # エクスポート自動化
│   ├── ai_feedback.py      # AI分析とフィードバック生成
│   ├── report_generator.py # Markdownレポート生成
│   └── cli.py              # CLIインターフェース
└── pyproject.toml          # uv + ruff + mypy設定

chrome-profile/              # 永続的Chromeプロファイル (自動生成、Git管理外)
downloads/                   # エクスポートファイル・レポート保存先 (自動生成)
  ├── tasks_*.csv           # エクスポートされたCSVファイル
  ├── charts/               # グラフ画像
  │   ├── project_analysis.png
  │   └── mode_analysis.png
  └── report_*.md           # 生成されたレポート
```

### 実行フロー

CLIツール (`app/src/tccretro/cli.py`) は以下を統括:

1. **ログイン状態確認** (`login.py`):
   - 永続的Chromeプロファイルを使用してブラウザを起動
   - TaskChute Cloudへ遷移し、ログイン済みかチェック
   - 未ログインの場合は手動ログインを促す
   - ログイン情報は `chrome-profile/` に自動保存

2. **エクスポート** (`export.py`):
   - エクスポートページ (`https://taskchute.cloud/export/csv-export`) へ遷移
   - 日付範囲入力フィールドに日付を入力
   - ダウンロードボタンをクリック
   - ダウンロードファイルを指定ディレクトリに保存

3. **データ分析** (`--analyze` オプション使用時):
   - CSVデータをpandasで読み込み
   - プロジェクト別・モード別の時間集計
   - グラフ生成 (PNG形式、日本語フォント対応)
   - Bedrock (Claude) によるAI分析とフィードバック生成
   - Markdownレポートの生成

### 重要な実装詳細

**永続的Chromeプロファイル:**

- `chrome-profile/` ディレクトリにブラウザの状態を保存
- 初回実行時に手動でログインすると、次回以降は自動的にログイン済み状態
- Google/Apple/メールいずれの認証方法でもOK
- リセットしたい場合は `chrome-profile/` を削除

**Playwrightセレクタ:**
`login.py` と `export.py` はTaskChute CloudのHTML構造が変わる可能性があるため**フォールバックセレクタパターン**を使用:

- ログイン確認: URLパターン (`/taskchute` かつ `/auth/` でない) とログインボタンの有無で判定
- エクスポート: 日付入力フィールド、ダウンロードボタンなど複数のセレクタパターンを試行

**セレクタ更新時:** TaskChute Cloudの実際のDOM構造を検証し、両ファイルのセレクタリストを更新すること。

**デバッグモード:**

- `--debug` オプションでブラウザを表示
- `export.py` はデバッグモード時にスクリーンショットを自動保存
- スクリーンショット保存先: `{output_dir}/debug_*.png`

## 設定ファイル

- `.pre-commit-config.yaml`: ruff, mypy, gitleaks, markdownlintを実行
- `app/pyproject.toml`: Python依存関係 + ruff/mypy設定 (行長: 100)
- `app/.env.example`: 環境変数テンプレート (永続的プロファイルを使う場合は不要)

## AI分析の設定

AI分析機能を使用する場合は、AWS認証情報が必要です:

```bash
# 環境変数で設定
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# または ~/.aws/credentials ファイルで設定
```

AI分析を無効化する場合は `--no-ai` フラグを使用してください。

### AI分析の高度な機能

AI分析は、以下の情報を自動的にプロンプトに含めて、より詳細なフィードバックを生成します：

1. **日付・休日情報の自動判定**
   - CSVファイル名または内容から分析対象の日付範囲を自動抽出
   - `jpholiday`ライブラリを使用して日本の祝日を判定
   - 土日・平日の判定も含めてプロンプトに提供
   - 例: "2025-11-03 (月曜日): 祝日 - 文化の日"

2. **CSVデータサンプルの提供**
   - 分析に必要なカラムのみを抽出してプロンプトに含める
   - 抽出されるカラム:
     - タイムライン日付、タスク名、プロジェクト名、モード名
     - ルーチン名、見積時間、実績時間、開始日時、終了日時
   - デフォルトで最大1000行まで提供（通常の1日分なら全行が含まれる）
   - 1000行を超える大量データの場合:
     - 警告ログが表示され、最初の1000行のみが使用される
     - より詳細な分析には日付範囲を絞って実行することを推奨
   - 生データを参照することで、AIがより具体的な洞察を提供可能

これらの機能により、AIは休日と平日の時間の使い方の違いや、具体的なタスクに基づいた改善提案を提供できます。

## 新しい分析観点の追加方法

拡張性のあるプラグインベース設計により、新しい分析観点を簡単に追加できます:

1. `app/src/tccretro/analyzer/` に新しいアナライザーを作成
2. `IAnalyzer` 基底クラスを継承
3. `analyze()` メソッドを実装
4. `report_generator.py` の `_register_analyzers()` に登録

例:

```python
from tccretro.analyzer.base import IAnalyzer, AnalysisResult

class TagAnalyzer(IAnalyzer):
    @property
    def name(self) -> str:
        return "tag"

    def analyze(self) -> AnalysisResult:
        # タグ別分析ロジック
        pass
```

## よくある問題

**ログイン/エクスポート失敗:**
TaskChute CloudのUI変更はCSSセレクタを破壊します。実際のページを検証後、`login.py` と `export.py` のセレクタリストを更新してください。

**ブラウザ起動失敗:**

- Chromiumがインストールされているか確認: `uv run playwright install chromium`
- システムのChromeブラウザが古い場合は更新

**Chromeプロファイルのリセット:**
認証情報をリセットしたい場合:

```bash
rm -rf chrome-profile/
uv run python -m tccretro.cli --login-only --debug
```

## セキュリティ注意事項

- 認証情報はローカルの `chrome-profile/` に保存 (Git管理外)
- `.gitignore` によりChromeプロファイルとダウンロードファイルは除外
- コードやgitに認証情報なし (gitleaks pre-commitフックで強制)
- 環境変数ファイル (`.env`) もGit管理外
