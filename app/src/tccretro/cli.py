"""TaskChute Cloudエクスポート自動化のためのCLIツール (ローカル実行)."""

import sys
from datetime import date, timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from tccretro.export import TaskChuteExporter
from tccretro.login import create_login_from_env


@click.command()
@click.option(
    "--login-only",
    is_flag=True,
    help="ログインテストのみ実行",
)
@click.option(
    "--export-only",
    is_flag=True,
    help="エクスポートのみ実行 (ログイン済み前提)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="デバッグモード (ブラウザを表示)",
)
@click.option(
    "--slow-mo",
    type=int,
    default=0,
    help="スローモーション実行 (ミリ秒)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="./downloads",
    help="ダウンロードファイルの保存先",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    default=".env",
    help=".envファイルのパス",
)
@click.option(
    "--export-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="エクスポート日付 (YYYY-MM-DD形式, デフォルト: 昨日)",
)
@click.option(
    "--export-start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="エクスポート開始日 (YYYY-MM-DD形式)",
)
@click.option(
    "--export-end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="エクスポート終了日 (YYYY-MM-DD形式)",
)
@click.option(
    "--analyze",
    is_flag=True,
    help="エクスポート後にデータ分析とレポート生成を実行",
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="AI分析を無効化（グラフと集計のみ生成）",
)
def main(
    login_only: bool,
    export_only: bool,
    debug: bool,
    slow_mo: int,
    output_dir: str,
    env_file: str,
    export_date: date | None,
    export_start_date: date | None,
    export_end_date: date | None,
    analyze: bool,
    no_ai: bool,
):
    """TaskChute Cloud エクスポート自動化ツール (ローカル実行)."""
    # Load environment variables
    load_dotenv(env_file)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Calculate export dates
    start_date: date
    end_date: date

    if export_date:
        # Single date specified
        start_date = export_date.date() if hasattr(export_date, "date") else export_date
        end_date = start_date
    elif export_start_date and export_end_date:
        # Range specified
        start_date = (
            export_start_date.date() if hasattr(export_start_date, "date") else export_start_date
        )
        end_date = export_end_date.date() if hasattr(export_end_date, "date") else export_end_date
    elif export_start_date or export_end_date:
        click.echo(
            "エラー: --export-start-date と --export-end-date は両方指定する必要があります",
            err=True,
        )
        sys.exit(1)
    else:
        # Default: yesterday
        yesterday = date.today() - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday

    click.echo("=== TaskChute Cloud Export Automation ===")
    click.echo(f"出力先: {output_path.absolute()}")
    click.echo(f"デバッグモード: {'ON' if debug else 'OFF'}")
    if not login_only:
        click.echo(f"エクスポート期間: {start_date} 〜 {end_date}")

    if login_only and export_only:
        click.echo("エラー: --login-only と --export-only は同時に指定できません", err=True)
        sys.exit(1)

    try:
        # Initialize components
        login_handler = create_login_from_env()

        # Run Playwright automation with persistent Chrome profile
        with sync_playwright() as p:
            # Create persistent profile directory
            profile_dir = Path("./chrome-profile")
            profile_dir.mkdir(parents=True, exist_ok=True)

            # Launch Chrome with persistent context
            click.echo("\n[0/2] Chrome を起動中...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=not debug,
                slow_mo=slow_mo,
                channel="chrome",  # Use system Chrome
                viewport={"width": 1920, "height": 1080},
                accept_downloads=True,
                locale="ja-JP",
                timezone_id="Asia/Tokyo",
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            page = context.new_page()

            try:
                # Determine total steps
                total_steps = 2
                if analyze and not login_only:
                    total_steps = 3

                # Step 1: Login
                if not export_only:
                    click.echo(f"\n[1/{total_steps}] TaskChute Cloudにログイン中...")
                    login_success = login_handler.login(page)

                    if not login_success:
                        click.echo("✗ ログイン失敗", err=True)
                        sys.exit(1)

                    click.echo("✓ ログイン成功")
                    click.echo("(認証情報は chrome-profile/ に自動保存されます)")

                    if login_only:
                        click.echo("\n=== ログインテスト完了 ===")
                        return

                # Step 2: Export
                if not login_only:
                    click.echo(f"\n[2/{total_steps}] データをエクスポート中...")
                    exporter = TaskChuteExporter(download_dir=str(output_path), debug=debug)
                    exported_file = exporter.export_data(
                        page, start_date=start_date, end_date=end_date
                    )

                    if not exported_file:
                        click.echo("✗ エクスポート失敗", err=True)
                        sys.exit(1)

                    click.echo(f"✓ エクスポート成功: {exported_file}")

                    # Step 3: Analyze (if requested)
                    if analyze:
                        click.echo("\n[3/3] データを分析中...")
                        try:
                            from tccretro.report_generator import ReportGenerator

                            generator = ReportGenerator(
                                csv_path=Path(exported_file),
                                output_dir=output_path,
                                enable_ai=not no_ai,
                            )
                            report_path = generator.generate_report()
                            click.echo(f"✓ 分析レポート生成完了: {report_path}")
                        except Exception as e:
                            click.echo(f"✗ 分析失敗: {e}", err=True)
                            if debug:
                                import traceback

                                traceback.print_exc()

                click.echo("\n=== すべての処理が完了しました ===")

            finally:
                page.close()
                context.close()

    except KeyboardInterrupt:
        click.echo("\n中断されました", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n✗ エラー: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
