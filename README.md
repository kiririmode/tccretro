# tccretro

TaskChute Cloud Export Automation - Playwrightを使用してTaskChute Cloudのデータをローカルに自動エクスポート

## 概要

このプロジェクトは、TaskChute Cloudからのデータエクスポートをローカル環境で自動化します:

- **Playwright** によるブラウザ自動化 (ログイン + エクスポートボタンクリック)
- **永続的Chromeプロファイル** による認証情報の保存
- **uv** によるPython依存関係管理
- **CSV形式** でのデータエクスポート

## アーキテクチャ

```text
CLI実行 → Playwright (永続的Chromeプロファイル) → TaskChute Cloud → ローカルファイル
```

### コンポーネント

- `app/src/tccretro/`: メインパッケージ
  - `login.py`: Playwrightログイン状態確認
  - `export.py`: エクスポート自動化
  - `cli.py`: コマンドラインインターフェース

## 前提条件

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - Pythonパッケージマネージャ
- TaskChute Cloudアカウント
- Chrome/Chromiumブラウザ (システムにインストール済み)

## セットアップ

### 1. リポジトリのクローンと依存関係インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd tccretro

# Python依存関係をインストール
cd app
uv sync

# Playwrightブラウザをインストール
uv run playwright install chromium

# pre-commitフックをインストール (オプション)
uv run pre-commit install
```

### 2. 環境変数の設定 (オプション)

環境変数ファイルは必須ではありませんが、参照用に作成できます:

```bash
cd app
cp .env.example .env
# .envファイルを編集 (ただし永続的プロファイルを使う場合は不要)
```

**注意**: 永続的Chromeプロファイルを使用するため、実際の認証はブラウザで手動で行います。

## 使用方法

### 初回実行: ログイン認証の保存

初回実行時は、ブラウザを表示して手動でログインします:

```bash
cd app
uv run python -m tccretro.cli --login-only --debug
```

ブラウザが起動したら:

1. TaskChute Cloudにログイン (Google/Apple/メールいずれでもOK)
2. ログインが完了したら、次回以降は自動的にログイン済みの状態で起動します
3. 認証情報は `chrome-profile/` ディレクトリに保存されます

### 通常実行: データのエクスポート

ログイン済みの状態でデータをエクスポートします:

```bash
# 基本的な実行 (昨日のデータをエクスポート)
uv run python -m tccretro.cli

# 特定の日付をエクスポート
uv run python -m tccretro.cli --export-date 2025-01-15

# 日付範囲を指定してエクスポート
uv run python -m tccretro.cli --export-start-date 2025-01-01 --export-end-date 2025-01-31

# 保存先を指定
uv run python -m tccretro.cli --output-dir ./my_exports

# デバッグモード (ブラウザを表示)
uv run python -m tccretro.cli --debug

# スローモーション実行 (動作確認用)
uv run python -m tccretro.cli --slow-mo 1000 --debug
```

### CLIオプション一覧

```bash
# ヘルプを表示
uv run python -m tccretro.cli --help
```

主なオプション:

- `--login-only`: ログインテストのみ実行
- `--export-only`: エクスポートのみ実行 (ログイン済み前提)
- `--debug`: デバッグモード (ブラウザを表示)
- `--slow-mo`: スローモーション実行 (ミリ秒)
- `--output-dir`: ダウンロードファイルの保存先 (デフォルト: `./downloads`)
- `--export-date`: エクスポート日付 (YYYY-MM-DD形式)
- `--export-start-date`: エクスポート開始日
- `--export-end-date`: エクスポート終了日
- `--env-file`: .envファイルのパス (デフォルト: `.env`)

## エクスポートされるファイル

エクスポートされたCSVファイルは以下の形式で保存されます:

```text
downloads/
└── taskchute_YYYYMMDD_HHMMSS.csv
```

## 開発

### コード品質

このプロジェクトはpre-commitフックを使用してコード品質を維持します:

```bash
# すべてのpre-commitフックを手動実行
uv run pre-commit run --all-files

# 特定のフックを実行
uv run pre-commit run ruff --all-files
```

### リンティングとフォーマット

**Python:**

```bash
# Pythonコードをフォーマット
uv run ruff format app/

# Pythonコードをリント
uv run ruff check app/ --fix

# 型チェック
uv run mypy app/src/
```

## プロジェクト構造

```text
tccretro/
├── app/                          # Pythonアプリケーション
│   ├── src/
│   │   └── tccretro/
│   │       ├── __init__.py
│   │       ├── login.py          # ログイン状態確認
│   │       ├── export.py         # エクスポート自動化
│   │       └── cli.py            # CLIインターフェース
│   ├── pyproject.toml            # uvプロジェクト設定
│   └── .env.example              # 環境変数テンプレート
├── chrome-profile/               # 永続的Chromeプロファイル (自動生成)
├── downloads/                    # エクスポートファイル保存先 (自動生成)
└── README.md                     # このファイル
```

## トラブルシューティング

### ログイン失敗

**症状**: ログインボタンが見つからない、またはログインできない

**対処法**:

1. `--login-only --debug` オプションを使用してブラウザを表示
2. 手動でログインを試行
3. TaskChute Cloud UIが変更されている場合は `login.py` のセレクタを更新

### エクスポート失敗

**症状**: エクスポートボタンが見つからない、またはダウンロードが開始されない

**対処法**:

1. `--debug` オプションを使用して画面を確認
2. スクリーンショットを確認 (デバッグモードで自動保存)
3. TaskChute Cloud UIが変更されている場合は `export.py` のセレクタを更新

### Chromeプロファイルのリセット

認証情報をリセットしたい場合:

```bash
# chrome-profile ディレクトリを削除
rm -rf chrome-profile/

# 再度ログイン
uv run python -m tccretro.cli --login-only --debug
```

## セキュリティに関する考慮事項

- 認証情報はローカルのChromeプロファイル (`chrome-profile/`) に保存されます
- `.gitignore` によりChromeプロファイルはGit管理外です
- pre-commitフックで秘密情報の誤コミットを検出 (gitleaks)

## 今後の拡張案

- 複数のエクスポート形式をサポート
- エクスポートデータの自動分析機能
- エクスポート履歴の管理
- スケジュール実行機能 (cron等との連携)

## ライセンス

MIT
