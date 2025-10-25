"""Amazon Bedrock (Claude) によるAI分析モジュール."""

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)


class AIFeedbackGenerator:
    """Amazon Bedrock (Claude) を使用してデータ分析とフィードバックを生成するクラス."""

    def __init__(self, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
        """AIFeedbackGeneratorを初期化する.

        Args:
            model_id: 使用するBedrockのモデルID
        """
        self.model_id = model_id
        self.bedrock_client = self._create_bedrock_client()

    def _create_bedrock_client(self) -> Any:
        """Bedrock Runtimeクライアントを作成する.

        環境変数からAWS認証情報を取得します。

        Returns:
            boto3.client: Bedrock Runtimeクライアント

        Raises:
            Exception: AWS認証情報が設定されていない場合
        """
        try:
            # AWS認証情報を環境変数から取得
            aws_region = os.getenv("AWS_REGION", "us-east-1")

            client = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_region,
            )
            logger.info("Bedrock Runtimeクライアントを初期化しました (region: %s)", aws_region)
            return client
        except Exception as e:
            logger.error("Bedrock Runtimeクライアントの初期化に失敗しました: %s", e)
            raise

    def generate_feedback(
        self, project_summary: dict[str, Any], mode_summary: dict[str, Any]
    ) -> str:
        """分析データをもとにAIフィードバックを生成する.

        Args:
            project_summary: プロジェクト別分析のサマリー
            mode_summary: モード別分析のサマリー

        Returns:
            str: 生成されたフィードバック（Markdown形式）
        """
        logger.info("AI分析を開始します")

        # プロンプトを構築
        prompt = self._build_prompt(project_summary, mode_summary)

        try:
            # Bedrock APIを呼び出し
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": 4000,
                    "temperature": 0.7,
                },
            )

            # レスポンスからテキストを抽出
            feedback = response["output"]["message"]["content"][0]["text"]
            logger.info("AI分析が完了しました")
            return feedback

        except Exception as e:
            logger.error("AI分析に失敗しました: %s", e)
            return self._generate_fallback_feedback(project_summary, mode_summary)

    def _build_prompt(self, project_summary: dict[str, Any], mode_summary: dict[str, Any]) -> str:
        """AI分析用のプロンプトを構築する.

        Args:
            project_summary: プロジェクト別分析のサマリー
            mode_summary: モード別分析のサマリー

        Returns:
            str: 構築されたプロンプト
        """
        project_data = json.dumps(project_summary, ensure_ascii=False, indent=2)
        mode_data = json.dumps(mode_summary, ensure_ascii=False, indent=2)

        prompt = f"""あなたは時間管理とライフスタイル改善のエキスパートです。
以下のTaskChute Cloudのデータ分析結果をもとに、より良い暮らしのための時間の使い方についての詳細なフィードバックを提供してください。

# プロジェクト別分析データ
```json
{project_data}
```

# モード別分析データ
```json
{mode_data}
```

以下の観点から分析とフィードバックを提供してください:

## 1. 現状分析
- 時間の使い方の傾向と特徴
- バランスの良い点と課題点
- 特に注目すべきプロジェクトやモード

## 2. 改善提案
- より良い時間配分のための具体的な提案
- ワークライフバランスの改善案
- 優先順位付けのアドバイス

## 3. アクションプラン
- 今週から実践できる具体的な行動
- 短期目標（1週間）と中期目標（1ヶ月）
- 進捗を測定する指標

回答はMarkdown形式で、見出しを使って構造化してください。
具体的で実践的なアドバイスを心がけてください。"""

        return prompt

    def _generate_fallback_feedback(
        self, project_summary: dict[str, Any], mode_summary: dict[str, Any]
    ) -> str:
        """AI分析が失敗した場合のフォールバックフィードバックを生成する.

        Args:
            project_summary: プロジェクト別分析のサマリー
            mode_summary: モード別分析のサマリー

        Returns:
            str: 基本的なフィードバック（Markdown形式）
        """
        lines = [
            "## AI分析結果",
            "",
            "> **注意**: AI分析サービスに接続できませんでした。基本的な分析結果を表示します。",
            "",
            "### プロジェクト別の傾向",
            "",
            f"- 合計 {project_summary.get('total_projects', 0)} プロジェクトで活動",
            f"- 総時間: {project_summary.get('total_hours', 0):.2f} 時間",
        ]

        top_project = project_summary.get("top_project")
        if top_project:
            top_hours = project_summary.get("top_project_hours", 0)
            lines.append(f"- 最も時間を使ったプロジェクト: **{top_project}** ({top_hours:.2f}時間)")

        lines.extend(
            [
                "",
                "### モード別の傾向",
                "",
                f"- 合計 {mode_summary.get('total_modes', 0)} モードで活動",
                f"- 総時間: {mode_summary.get('total_hours', 0):.2f} 時間",
            ]
        )

        top_mode = mode_summary.get("top_mode")
        if top_mode:
            top_mode_hours = mode_summary.get("top_mode_hours", 0)
            lines.append(f"- 最も時間を使ったモード: **{top_mode}** ({top_mode_hours:.2f}時間)")

        lines.extend(
            [
                "",
                "### 推奨事項",
                "",
                "- 時間配分を定期的に見直しましょう",
                "- バランスの取れた生活を心がけましょう",
                "- 優先順位の高いタスクに集中しましょう",
                "",
            ]
        )

        return "\n".join(lines)
