<div align="center">

# Website Uptime Monitor

### AWSサーバーレス稼働監視システム｜個人開発・本番運用中

[![ライブダッシュボード](https://img.shields.io/badge/🟢_ライブダッシュボード-開く-2ea44f?style=for-the-badge)](https://amanrai00-uptime-dashboard.s3.ap-northeast-1.amazonaws.com/index.html)
[![English](https://img.shields.io/badge/English-README.md-red?style=for-the-badge)](README.md)

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=flat&logo=amazon-aws&logoColor=white)
![Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat&logo=awslambda&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?style=flat&logo=amazondynamodb&logoColor=white)
![S3](https://img.shields.io/badge/Amazon_S3-569A31?style=flat&logo=amazons3&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)

---

**5分ごとにLambdaが対象サイトを巡回 → コンテンツ検証（HTTP 200だけで判定しない）→ DynamoDBに記録 → S3静的ダッシュボードで可視化 → 連続障害時のみSNSメール通知**

EC2なし。API Gatewayなし。常時稼働コンピュートなし。月額約0円。

</div>

---

## 解決したい課題

HTTP 200 ≠ サイト正常。CloudFrontのエラーページ、メンテナンスページ、デプロイ失敗時の表示も全てHTTP 200を返します。基本的な稼働監視ではこれらを見逃します。

本システムは**ステータスコードだけでなくコンテンツも検証**します。

---

## アーキテクチャ

<div align="center">

![Architecture](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.png.PNG)

</div>

```
EventBridge (5分ごと) ──► Lambda ──┬──► DynamoDB（履歴）
                                    ├──► S3 status.json ──► 静的ダッシュボード
                                    └──► SNSメール（連続N回障害時のみ）
```

| 設計判断 | 理由 |
|---|---|
| **Lambda（EC2ではなく）** | スケジュール実行のみ、常時稼働なし、パッチ適用不要 |
| **DynamoDB（RDSではなく）** | 追記型のタイムスタンプ書き込み、スキーマ変更管理が不要 |
| **S3 `status.json`（API Gatewayではなく）** | 静的ファイル1つで完結、バックエンド不要、コールドスタートなし |
| **SNS（独自メール送信ではなく）** | AWS側で配信を担保、運用するインフラがゼロ |
| **連続障害しきい値** | 一時的な単発障害ではアラートを出さない。アラートの信頼性を維持 |

---

## スクリーンショット

<table>
  <tr>
    <td align="center"><b>ダッシュボード（正常時）</b></td>
    <td align="center"><b>ダッシュボード（障害検知時）</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png" /></td>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png" /></td>
  </tr>
  <tr>
    <td align="center"><b>DynamoDB チェック履歴</b></td>
    <td align="center"><b>SNSアラートメール</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png" /></td>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png" /></td>
  </tr>
</table>

---

## 構築・運用を通じて得た学び

> **HTTP 200は信用できない。** メンテナンスページもCloudFrontのエラーページもHTTP 200を返します。コンテンツ検証こそがこのシステムで最も実用的な機能になりました。

> **`status.json`とDynamoDBが静かに食い違う問題に直面しました。** ダッシュボードはDOWN表示なのに`recent_failures`は空のまま。原因はLambdaが過去のDynamoDBレコードを参照する一方で、現在の障害結果をS3ペイロードに反映していないこと。修正：現在のチェック結果を先に書き込み → 過去の障害をDynamoDBから取得 → `check_time`で重複排除 → 最新5件を保持。実際に運用しなければ気付けないバグでした。

> **IAMの最小権限設計は思考の訓練。** 各権限を特定のARN（DynamoDBテーブル、SNSトピック、S3の特定キー）にスコープすることで、各サービスが本当に必要としているものを明確に理解できました。本番運用にもそのまま活きる視点です。

> **アラートノイズは見逃しよりも信頼を損なう。** 単発の一時障害で毎回メールが飛ぶと、運用者はアラートを無視するようになります。連続障害しきい値2を設定することで、アラートの信頼性が大きく向上しました。

> **読み取り専用ダッシュボードはAPI GatewayよりS3が優位。** 読み取り経路でのコールドスタートなし。トレードオフはダッシュボードの鮮度が直近のLambda実行時刻に依存する点（最大5分）。本用途では許容可能と判断しました。

---

## 障害検知ロジック

上から順に評価。最初にマッチしたルールで失敗判定。

| # | ルール | 検知条件 |
|---|---|---|
| 1 | ネットワークエラー | 接続拒否 / DNS失敗 / タイムアウト |
| 2 | ステータスコード異常 | HTTP 200〜299の範囲外 |
| 3 | 応答遅延 | 応答時間が`RESPONSE_THRESHOLD_MS`を超過 |
| 4 | 期待コンテンツ欠落 | `EXPECTED_TEXT`設定済みだがレスポンス本文に存在しない |
| 5 | 禁止コンテンツ検出 | `FORBIDDEN_TEXT`設定済みでレスポンス本文に存在 |
| 6 | リダイレクトブロック | `redirect_policy=fail_on_redirect`でリダイレクト検出 |

---

## アラートフロー

```
障害1回目  →  DynamoDBに記録のみ。メール送信なし。
障害2回目  →  SNSメール送信（URL、原因、ステータス、応答時間、タイムスタンプ）
回復時    →  consecutive_failure_count を 0 にリセット
```

デフォルトしきい値：**2**。`ALERT_FAILURE_THRESHOLD`で設定変更可能。

---

## 複数サイト監視

1回のLambda実行で複数サイトを監視可能。各サイトはDynamoDB上で独自の`site_id`を持ち、テーブルは1つで共有。

各実行ごとに記録されるサイト別メトリクス：
- 稼働率（%）
- 平均応答時間
- インシデント件数（直近24時間 / 7日間）
- 連続障害カウント
- アラート送信フラグ
- リダイレクトポリシー・検出状況

---

## コスト

**月額約0円**

| リソース | 月間使用量 | 無料枠内？ |
|---|---|---|
| Lambda実行回数 | 約8,640回 | ✅ 余裕で内 |
| DynamoDB書き込み | サイトあたり約8,640回 | ✅ オンデマンド、余裕で内 |
| S3 PUT（`status.json`） | 約8,640回（各約1KB） | ✅ 余裕で内 |
| SNSメール | 連続障害時のみ | ✅ ほぼゼロ |

常時稼働コンピュートなし。スケジュール実行のみ。

---

## セットアップ

<details>
<summary><b>クリックして展開</b></summary>

### 前提条件
- AWSアカウント
- Python 3.12以上
- リージョン：`ap-northeast-1`

### AWSリソース

| リソース | 名称 |
|---|---|
| DynamoDBテーブル | `website_checks` |
| SNSトピック | `uptime-alerts` |
| IAMロール | `uptime-monitor-lambda-role` |
| Lambda関数 | `website-uptime-check` |
| EventBridgeルール | `uptime-check-every-5-min` |
| S3バケット | グローバルにユニークな名称 |

### 環境変数（単一サイト構成）

| 変数 | 説明 | デフォルト |
|---|---|---|
| `TARGET_URL` | 監視対象URL | 必須 |
| `TIMEOUT_SECONDS` | リクエストタイムアウト | `10` |
| `RESPONSE_THRESHOLD_MS` | 許容応答時間の上限 | `3000` |
| `SNS_TOPIC_ARN` | 障害通知先のARN | 必須 |
| `DYNAMODB_TABLE` | テーブル名 | `website_checks` |
| `S3_BUCKET` | ダッシュボードのバケット名 | 必須 |
| `S3_STATUS_KEY` | ステータスファイルのキー | `status.json` |
| `SITE_ID` | チェックごとに記録される識別子 | `my-portfolio` |
| `EXPECTED_TEXT` | レスポンス本文に必須の文字列 | 任意 |
| `FORBIDDEN_TEXT` | レスポンス本文に存在してはならない文字列 | 任意 |
| `ALERT_FAILURE_THRESHOLD` | アラート送信までの連続障害回数 | `2` |
| `RETENTION_DAYS` | DynamoDB TTL保持期間（日） | `30` |
| `REDIRECT_POLICY` | `follow` または `fail_on_redirect` | `follow` |

### 複数サイト構成（`SITES_CONFIG`）

JSON配列で指定。指定時は単一サイト構成より優先。

```json
[
  {
    "site_id": "main-site",
    "target_url": "https://example.com",
    "timeout_seconds": 10,
    "response_threshold_ms": 3000,
    "expected_text": "Welcome",
    "forbidden_text": "Error",
    "redirect_policy": "follow"
  },
  {
    "site_id": "second-site",
    "target_url": "https://example.org"
  }
]
```

### デプロイ

```bash
cd lambda
zip -r ../lambda-deploy.zip .

aws lambda update-function-code \
  --function-name website-uptime-check \
  --zip-file fileb://../lambda-deploy.zip

aws s3 sync dashboard/ s3://your-bucket-name/
```

### 動作確認テスト

- ✅ 正常URL → `is_success: true`、SNS送信なし
- ✅ 障害URL → `is_success: false`、2回連続障害でSNSメール送信
- ✅ 低い`RESPONSE_THRESHOLD_MS` → 応答遅延として検知
- ✅ `EXPECTED_TEXT`不一致 → HTTP 200でもコンテンツ障害として検知
- ✅ `SITES_CONFIG`複数指定 → `site_id`ごとに独立したアイテム生成

</details>

---

## DynamoDBスキーマ

<details>
<summary><b>クリックして展開</b></summary>

```
website_checks
├── site_id                       (パーティションキー)
├── check_time                    (ソートキー、ISO 8601)
├── url
├── status_code
├── response_time_ms
├── is_success
├── failure_reason
├── content_check_passed
├── uptime_percentage
├── uptime_window_checks
├── average_response_time_ms
├── response_time_window_checks
├── incident_count_24h
├── incident_count_7d
├── consecutive_failure_count
├── alert_sent
├── alert_failure_threshold
├── redirect_policy
├── redirect_detected
└── ttl_expires_at
```

</details>

---

## IAM（最小権限の原則）

| 権限 | スコープ |
|---|---|
| `dynamodb:PutItem` | `website_checks`のARNのみ |
| `dynamodb:Query` | `website_checks`のARNのみ |
| `sns:Publish` | `uptime-alerts`のARNのみ |
| `s3:PutObject` | `<bucket>/status.json`のみ |
| CloudWatch Logs | Lambda実行ログのみ |

アプリケーションの主要な権限は特定のリソースにスコープしています。DynamoDB・SNS・S3は、対象のテーブル・トピック・`status.json`オブジェクトに限定。CloudWatch Logsの権限はLambdaのログ出力に限定しています。

---

## CloudWatchログ

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

---

## 既知の制約

- ダッシュボードは直近の`status.json`書き込み時点を表示（リアルタイムストリームではない）。鮮度はタイムスタンプで確認可能。
- ダッシュボードに認証なし。ポートフォリオ用途では許容、本番では非推奨。
- LambdaやEventBridgeが静かに停止した場合のデッドマンスイッチなし。CloudWatchの実行回数アラームで補完可能。
- アラートしきい値はグローバル1つのみ。サイトごとの個別設定は未対応。
- ダッシュボードのチャートは現在の`status.json`のみ参照するため、応答時間の履歴グラフは未表示。

---

## ロードマップ

- [ ] Lambdaの静かな停止を検知するCloudWatchアラーム（デッドマンスイッチ）
- [ ] サイトごとのアラートしきい値設定
- [ ] Terraform / AWS SAMによるIaCデプロイ

---

## プロジェクト構成

```
website-uptime-monitor/
├── lambda/
│   ├── app.py
│   ├── requirements.txt
│   └── tests/
│       └── test_app.py
├── dashboard/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── docs/
    ├── architecture.png
    └── screenshots/
```

---

<div align="center">

### 開発者：[ライ アマン](https://www.linkedin.com/in/amanrai00) ／ 東京

**AWS認定クラウドプラクティショナー（CLF-C02）取得済み** ・ SAA-C03取得に向けて学習中 ・ クラウドエンジニアを目指して構築中

[LinkedIn](https://www.linkedin.com/in/amanrai00) ・ [GitHub](https://github.com/amanrai00) ・ [AWS認定バッジ](https://www.credly.com/badges/095a2b8e-c94f-4af6-b77c-51ec2fa64d56)

</div>
