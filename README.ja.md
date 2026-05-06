# ウェブサイト稼働監視システム

[English version here](README.md)

> サーバーレスAWS監視エンジン。稼働確認、コンテンツ検証、障害アラート、静的ダッシュボードへのステータス公開を実現します。サーバー不要。運用コストはほぼゼロ。

![アーキテクチャ](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.ja.png.PNG)

-----

## 概要

5分ごとにLambda関数が起動し、設定されたすべての対象URLにアクセスして、サイトごとに4つの判断を行います。

1. レスポンスは返ってきたか？
1. レスポンス速度は許容範囲内か？
1. ページに表示されるべきコンテンツが存在するか？
1. ページに表示されてはいけないコンテンツが存在しないか？

結果はDynamoDBに保存されます。サイトが連続して失敗した場合、SNSメールが送信されます。最新のステータスはS3上の`status.json`ファイルに上書き保存され、静的ダッシュボードが読み込みます。API Gatewayは不要で、管理するサーバーもありません。

-----

## ダッシュボード

|マルチサイトダッシュボード|障害状態（DOWN）|
|---|---|
|![UP](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png)|![DOWN](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png)|

|DynamoDB 監視履歴|SNS アラートメール|
|---|---|
|![DynamoDB](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png)|![SNS](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png)|

-----

## 仕組み

```
EventBridge（5分ごと）
        │
        ▼
   Lambda 関数
   ┌──────────────────────────────────────┐
   │  設定されたサイトごとに：              │
   │  HTTP GET → 対象URL                  │
   │  ✓ ステータスコードが2xx？            │
   │  ✓ レスポンス時間が閾値以内？          │
   │  ✓ 期待テキストが存在する？            │
   │  ✓ 禁止テキストが存在しない？          │
   │  ✓ アラート閾値に達した？              │
   └──────────────────────────────────────┘
        │                   │
        ▼                   ▼
   DynamoDB            S3 status.json ──→ 静的ダッシュボード
   （全履歴）
        │
        ▼  連続失敗閾値到達時のみ
   SNS メールアラート
```

**このスタックを選んだ理由:**

- **Lambda（EC2ではなく）:** スケジュール実行のみで、アイドル課金なし、パッチ管理不要
- **DynamoDB（RDSではなく）:** スキーママイグレーション不要で、追記専用のタイムスタンプ付きデータ保存に適している
- **S3 `status.json`（API Gatewayではなく）:** ダッシュボードは静的ファイル1つを読むだけ。バックエンド運用不要
- **SNS（カスタムメールではなく）:** 連続失敗閾値到達後にメールアラート。配信はAWSが管理し、インフラ構築不要

-----

## 障害検知ルール

以下のいずれかに該当する場合、チェックは失敗とみなされます（上から順に評価）。

| ルール | 条件 |
|---|---|
| ネットワークエラー | 接続拒否、DNS障害、タイムアウト |
| 不正なステータスコード | 200〜299以外のHTTPレスポンス |
| レスポンス遅延 | レスポンス時間が`RESPONSE_THRESHOLD_MS`を超過 |
| コンテンツ不足 | `EXPECTED_TEXT`が設定されているがレスポンスボディに存在しない |
| 禁止コンテンツ検出 | `FORBIDDEN_TEXT`が設定されており、レスポンスボディに存在する |
| リダイレクトブロック | `redirect_policy`が`fail_on_redirect`に設定されており、リダイレクトが検出された |

コンテンツ検証は基本的な稼働監視に対する重要な追加機能です。メンテナンスページや壊れたデプロイでもHTTP 200を返す場合があります。期待テキストの確認により、ステータスコードだけでは検知できない障害を捕捉できます。

-----

## アラート

アラートはSNS送信前に連続失敗の閾値を使用します。デフォルトの閾値は2回です。

- 1回目の失敗: 記録・追跡されますが、アラートは送信されません
- 2回目の連続失敗: サイトURL、失敗理由、ステータスコード、レスポンスタイム、タイムスタンプを含むSNSメールが送信されます
- 復旧時: 連続失敗カウントが0にリセットされます

これにより、一時的な障害によるアラートノイズを削減しながら、実際の障害を確実に検知できます。

-----

## マルチサイト監視

`SITES_CONFIG`環境変数を使用して、1回のLambda実行で複数サイトを監視できます。各サイトはDynamoDBで独自の`site_id`を持ちます。すべての結果は1つのテーブルで管理されます。

毎回の実行でサイトごとに追跡するメトリクス:

- 稼働率
- 平均レスポンスタイム
- 直近24時間・7日間のインシデント数
- 連続失敗回数
- アラート送信済みステータス
- リダイレクトポリシーとリダイレクト検出状況

-----

## コスト

個人利用での想定コストは**ほぼ0円/月**です。

5分間隔での実行: 月約8,640回のLambda実行、サイトごとに約8,640回のDynamoDB書き込み、`status.json`ファイル（約1KB）を毎回上書き。この個人デモ用のワークロードでは、主要なAWS無料枠の上限を大幅に下回ります。SNSメールアラートは連続失敗時のみ送信されるため、その使用量も最小限に抑えられます。

コストを低く保つ設計: 常時稼働のコンピューティングリソースなし、ホスティングサーバーの代わりにS3静的ダッシュボードを使用、DynamoDBはオンデマンド課金、Lambdaはスケジュール実行のみ。

-----

## セットアップ

### 前提条件

- AWSアカウント
- Python 3.12以上
- リージョン: `ap-northeast-1`

### AWSリソース

| リソース | 名前 |
|---|---|
| DynamoDBテーブル | `website_checks` |
| SNSトピック | `uptime-alerts` |
| IAMロール | `uptime-monitor-lambda-role` |
| Lambda関数 | `website-uptime-check` |
| EventBridgeルール | `uptime-check-every-5-min` |
| S3バケット | グローバルで一意の任意の名前 |

### Lambda 環境変数

**シングルサイト設定:**

| 変数名 | 説明 | デフォルト値 |
|---|---|---|
| `TARGET_URL` | 監視対象のURL | 必須 |
| `TIMEOUT_SECONDS` | リクエストタイムアウト（秒） | `10` |
| `RESPONSE_THRESHOLD_MS` | 許容最大レスポンス時間（ミリ秒） | `3000` |
| `SNS_TOPIC_ARN` | 障害アラート用のARN | 必須 |
| `DYNAMODB_TABLE` | テーブル名 | `website_checks` |
| `S3_BUCKET` | ダッシュボード用バケット名 | ダッシュボード利用時は必須 |
| `S3_STATUS_KEY` | ステータスファイルのキー | `status.json` |
| `SITE_ID` | 各チェックに紐付けられる識別子 | `my-portfolio` |
| `EXPECTED_TEXT` | レスポンスボディに必ず含まれるべきテキスト | 任意 |
| `FORBIDDEN_TEXT` | レスポンスボディに含まれてはいけないテキスト | 任意 |
| `ALERT_FAILURE_THRESHOLD` | SNSアラート送信までの連続失敗回数 | `2` |
| `RETENTION_DAYS` | DynamoDB TTLの保持期間（日） | `30` |
| `REDIRECT_POLICY` | `follow`または`fail_on_redirect` | `follow` |

**マルチサイト設定:**

`SITES_CONFIG`をJSON配列で設定します。設定されている場合、シングルサイト変数より優先されます。

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
    "target_url": "https://example.org",
    "timeout_seconds": 10,
    "response_threshold_ms": 3000
  }
]
```

### デプロイ

```bash
# Lambdaパッケージ作成
cd lambda
zip -r ../lambda-deploy.zip .

# Lambdaにアップロード
aws lambda update-function-code \
  --function-name website-uptime-check \
  --zip-file fileb://../lambda-deploy.zip

# ダッシュボードをS3にアップロード
aws s3 sync dashboard/ s3://your-bucket-name/
```

### 動作確認

スケジュール実行に移行する前に、以下のLambda手動テストを実施してください。

- 正常URL: DynamoDBに`is_success: true`が記録され、SNSアラートが送信されないこと
- 障害URL: DynamoDBに`is_success: false`が記録され、2回連続失敗後にSNSメールが受信されること
- 低い`RESPONSE_THRESHOLD_MS`: レスポンス遅延が検知され、`is_success: false`になること
- 不一致の`EXPECTED_TEXT`: HTTP 200でもコンテンツ障害として`is_success: false`になること
- 複数サイトの`SITES_CONFIG`: `site_id`ごとに別のDynamoDBアイテムが作成されること

-----

## DynamoDB スキーマ

```
website_checks
├── site_id                      （パーティションキー）
├── check_time                   （ソートキー、ISO 8601形式）
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

-----

## IAMポリシー（最小権限の原則）

Lambdaロールには必要最低限の権限のみを付与しています。

| 権限 | スコープ |
|---|---|
| `dynamodb:PutItem` | `website_checks` ARNのみ |
| `dynamodb:Query` | `website_checks` ARNのみ |
| `sns:Publish` | `uptime-alerts` ARNのみ |
| `s3:PutObject` | `<バケット>/status.json`のみ |
| CloudWatch Logs 書き込み | Lambda実行ログ |

広範なアプリケーション権限は付与していません。DynamoDB、SNS、S3はそれぞれ特定のARNにスコープされています。

-----

## CloudWatch ログ

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

-----

## 既知の制限事項

- ダッシュボードはリアルタイムではなく、最後の`status.json`書き込み時点の状態を反映します。最終確認時刻のタイムスタンプにより、データの鮮度を確認できます。
- ダッシュボードに認証機能はありません。ポートフォリオ・デモ用途としては許容範囲ですが、本番環境では適切ではありません。
- LambdaやEventBridgeが静かに停止した場合の検知手段がありません。CloudWatchの実行回数アラームでこの問題を解決できます。
- 連続失敗アラート閾値は全サイト共通の単一値です。サイトごとの個別設定には対応していません。
- ダッシュボードのチャートはサイトごとの最新レスポンスタイムを表示しており、完全な履歴トレンドではありません。現在の`status.json`ペイロードのみを読み込むためです。

-----

## 学んだこと

**HTTP 200だけでは不十分。** CloudFrontのエラーページ、メンテナンスページ、壊れたデプロイはすべてHTTP 200を返すことがあります。コンテンツ検証により、ステータスコードだけでは検知できない障害を捕捉できます。これがPhase 3の本質的な価値です。

**`status.json`とDynamoDBは静かに乖離する可能性がある。** ダッシュボードはDOWNを表示しているのに`recent_failures`が空のままという問題が発生しました。LambdaがDynamoDBの過去レコードをクエリしていたものの、現在の障害チェック結果をS3ペイロードに注入していなかったことが原因でした。解決策: 現在の障害チェック結果を直接`recent_failures`に書き込み、その後DynamoDBから過去の障害を取得し、`check_time`で重複排除して最新5件を保持します。

**読み取り専用ダッシュボードにはS3がAPI Gatewayより適している。** ファイル1つで、バックエンドなし、読み取りパスにコールドスタートなし。唯一のトレードオフはリアルタイム性です。ダッシュボードは最後のLambda実行時点の状態を反映します。

**個人プロジェクトでもIAMのスコープ設定は重要。** 権限を特定のARNに絞ることで、各サービスが実際に必要とする権限を明確に理解でき、その考え方はシステム設計の面接でも直接活かせます。

**アラートノイズは実際の問題。** 1回の一時的な障害でSNSメールが届くと、アラートを無視する習慣がついてしまいます。連続失敗の閾値を追加するだけで、システムの信頼性が大幅に向上します。

-----

## 今後の改善案

- Lambdaが静かに停止した場合を検知するCloudWatchアラーム
- リージョン間のレイテンシ比較のためのマルチリージョン監視
- 5分のポーリング間隔では不十分になった場合のAPI Gatewayによるリアルタイムダッシュボード
- ログイン認証が必要なページの監視
- サイトごとの個別アラート閾値設定
- 内部ダッシュボードとは別の公開ステータスページ
- インフラのコード化のためのTerraformまたはAWS SAM

-----

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

-----

## 面接想定質問

このプロジェクトで答えられるように設計した質問:

- EC2上のcronジョブではなくLambdaを選んだ理由は？
- 監視データにRDSではなくDynamoDBを使った理由は？
- API GatewayではなくS3上の`status.json`を使った理由は？
- IAMポリシーで許可している内容と、それ以上の権限を付与しない理由は？
- `response_time_ms`はどのように計測され、何を意味するか？
- コンテンツ検証はHTTPステータスコードでは検知できない何を捕捉できるか？
- Lambdaが静かに停止した場合はどうなるか？
- 50サイトの監視に拡張するにはどうするか？
- アラート送信前に連続失敗の閾値を使う理由は？
- 1つのDynamoDBテーブルでマルチサイト監視はどのように機能するか？
