# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

TaskChute Cloud Export Automation: Playwrightブラウザ自動化を使用してTaskChute Cloudのデータをローカルに自動エクスポートするツール。

**アーキテクチャフロー:**
CLI実行 → Playwright (永続的Chromeプロファイル) → TaskChute Cloud (ログイン確認 + エクスポート) → ローカルファイル

## 技術スタック

- **Python 3.10+** - **uv** (パッケージマネージャ)で管理
- **Playwright** - ブラウザ自動化 (Chromium)
- **永続的Chromeプロファイル** - 認証情報の保存

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

# 特定の日付をエクスポート
uv run python -m tccretro.cli --export-date 2025-01-15

# 日付範囲を指定
uv run python -m tccretro.cli --export-start-date 2025-01-01 --export-end-date 2025-01-31

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
│   ├── login.py            # Playwrightログイン状態確認
│   ├── export.py           # エクスポート自動化
│   └── cli.py              # CLIインターフェース
└── pyproject.toml          # uv + ruff + mypy設定

chrome-profile/              # 永続的Chromeプロファイル (自動生成、Git管理外)
downloads/                   # エクスポートファイル保存先 (自動生成)
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
