# ウェブサイト稼働監視システム

[English version here](README.md)

> サーバーレスAWS監視エンジン。稼働確認、コンテンツ検証、障害アラート、静的ダッシュボードへのステータス公開を実現します。サーバー不要。運用コストはほぼゼロ。

![アーキテクチャ](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.png)

-----

## 概要

5分ごとにLambda関数が起動し、対象URLにアクセスして4つの判断を行います。

1. レスポンスは返ってきたか？
1. レスポンス速度は許容範囲内か？
1. ページに表示されるべきコンテンツが存在するか？
1. ページに表示されてはいけないコンテンツが存在しないか？

結果はDynamoDBに保存されます。障害が発生した場合、SNSメールが即座に送信されます。最新のステータスはS3上の`status.json`ファイルに上書き保存され、静的ダッシュボードが読み込みます。API Gatewayは不要で、管理するサーバーもありません。

-----

## ダッシュボード

|正常状態（UP）                                                                                                        |障害状態（DOWN）                                                                                                          |
|----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
|![UP](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png)|![DOWN](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png)|

|DynamoDB 監視履歴                                                                                                             |SNS アラートメール                                                                                                         |
|--------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
|![DynamoDB](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png)|![SNS](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png)|

-----

## 仕組み

```
EventBridge（5分ごと）
        │
        ▼
   Lambda 関数
   ┌──────────────────────────────┐
   │  HTTP GET → 対象URL           │
   │  ✓ ステータスコードが2xx？     │
   │  ✓ レスポンス時間が閾値以内？  │
   │  ✓ 期待テキストが存在する？    │
   │  ✓ 禁止テキストが存在しない？  │
   └──────────────────────────────┘
        │                   │
        ▼                   ▼
   DynamoDB            S3 status.json ──→ 静的ダッシュボード
   （全履歴）
        │
        ▼  障害時のみ
   SNS メールアラート
```

**このスタックを選んだ理由:**

- **Lambda（EC2ではなく）:** スケジュール実行のみで、アイドル課金なし、パッチ管理不要
- **DynamoDB（RDSではなく）:** スキーママイグレーション不要で、追記専用のタイムスタンプ付きデータ保存に適している
- **S3 `status.json`（API Gatewayではなく）:** ダッシュボードは静的ファイル1つを読むだけ。バックエンド運用不要
- **SNS（カスタムメールではなく）:** 障害時のみメールアラート。配信はAWSが管理し、インフラ構築不要

-----

## 障害検知ルール

以下のいずれかに該当する場合、チェックは失敗とみなされます（上から順に評価）。

|ルール        |条件                                    |
|-----------|--------------------------------------|
|ネットワークエラー  |接続拒否、DNS障害、タイムアウト                     |
|不正なステータスコード|200〜299以外のHTTPレスポンス                   |
|レスポンス遅延    |レスポンス時間が`RESPONSE_THRESHOLD_MS`を超過    |
|コンテンツ不足    |`EXPECTED_TEXT`が設定されているがレスポンスボディに存在しない|
|禁止コンテンツ検出  |`FORBIDDEN_TEXT`が設定されており、レスポンスボディに存在する|

コンテンツ検証は基本的な稼働監視に対する重要な追加機能です。メンテナンスページや壊れたデプロイでもHTTP 200を返す場合があります。期待テキストの確認により、ステータスコードだけでは検知できない障害を捕捉できます。

-----

## コスト

個人利用での想定コストは**ほぼ0円/月**です。

5分間隔での実行: 月約8,640回のLambda実行、約8,640回のDynamoDB書き込み、`status.json`ファイル（約1KB）を毎回上書き。この個人デモ用のワークロードでは、主要なAWS無料枠の上限を大幅に下回ります。SNSメールアラートは実際の障害時のみ送信されるため、その使用量も最小限に抑えられます。

コストを低く保つ設計: 常時稼働のコンピューティングリソースなし、ホスティングサーバーの代わりにS3静的ダッシュボードを使用、DynamoDBはオンデマンド課金、Lambdaはスケジュール実行のみ。

-----

## セットアップ

### 前提条件

- AWSアカウント
- Python 3.12以上
- リージョン: `ap-northeast-1`

### AWSリソース

|リソース          |名前                          |
|--------------|----------------------------|
|DynamoDBテーブル  |`website_checks`            |
|SNSトピック       |`uptime-alerts`             |
|IAMロール        |`uptime-monitor-lambda-role`|
|Lambda関数      |`website-uptime-check`      |
|EventBridgeルール|`uptime-check-every-5-min`  |
|S3バケット        |グローバルで一意の任意の名前              |

### Lambda 環境変数

|変数名                    |説明                    |デフォルト値          |
|-----------------------|----------------------|----------------|
|`TARGET_URL`           |監視対象のURL              |必須              |
|`TIMEOUT_SECONDS`      |リクエストタイムアウト（秒）        |`10`            |
|`RESPONSE_THRESHOLD_MS`|許容最大レスポンス時間（ミリ秒）      |`3000`          |
|`SNS_TOPIC_ARN`        |障害アラート用のARN           |必須              |
|`DYNAMODB_TABLE`       |テーブル名                 |`website_checks`|
|`S3_BUCKET`            |ダッシュボード用バケット名         |ダッシュボード利用時は必須   |
|`S3_STATUS_KEY`        |ステータスファイルのキー          |`status.json`   |
|`SITE_ID`              |各チェックに紐付けられる識別子       |`my-portfolio`  |
|`EXPECTED_TEXT`        |レスポンスボディに必ず含まれるべきテキスト |任意              |
|`FORBIDDEN_TEXT`       |レスポンスボディに含まれてはいけないテキスト|任意              |

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
- 障害URL: DynamoDBに`is_success: false`が記録され、SNSメールが受信されること
- 低い`RESPONSE_THRESHOLD_MS`: レスポンス遅延が検知され、SNSメールが受信されること
- 不一致の`EXPECTED_TEXT`: HTTP 200でもコンテンツ障害として`is_success: false`になること

-----

## DynamoDB スキーマ

```
website_checks
├── site_id              （パーティションキー）
├── check_time           （ソートキー、ISO 8601形式）
├── url
├── status_code
├── response_time_ms
├── is_success
├── failure_reason
└── content_check_passed
```

-----

## IAMポリシー（最小権限の原則）

Lambdaロールには必要最低限の権限のみを付与しています。

|権限                  |スコープ                  |
|--------------------|----------------------|
|`dynamodb:PutItem`  |`website_checks` ARNのみ|
|`dynamodb:Query`    |`website_checks` ARNのみ|
|`sns:Publish`       |`uptime-alerts` ARNのみ |
|`s3:PutObject`      |`<バケット>/status.json`のみ|
|CloudWatch Logs 書き込み|Lambda実行ログ            |

広範なアプリケーション権限は付与していません。DynamoDB、SNS、S3はそれぞれ特定のARNにスコープされています。

-----

## CloudWatch ログ

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

-----

## 既知の制限事項

- 現在は1つの対象URLのみを監視しています。マルチサイト対応は次の自然なステップで、各サイトに固有の`site_id`を割り当てることで実現できます。
- ダッシュボードはリアルタイムではなく、最後の`status.json`書き込み時点の状態を反映します。最終確認時刻のタイムスタンプにより、データの鮮度を確認できます。
- 障害ごとにアラートが送信されます。連続障害の閾値設定によるノイズ削減は改善予定です。
- ダッシュボードに認証機能はありません。ポートフォリオ・デモ用途としては許容範囲ですが、本番環境では適切ではありません。
- LambdaやEventBridgeが静かに停止した場合の検知手段がありません。CloudWatchの実行回数アラームでこの問題を解決できます。

-----

## 学んだこと

**HTTP 200だけでは不十分。** CloudFrontのエラーページ、メンテナンスページ、壊れたデプロイはすべてHTTP 200を返すことがあります。コンテンツ検証により、ステータスコードだけでは検知できない障害を捕捉できます。これがPhase 3の本質的な価値です。

**`status.json`とDynamoDBは静かに乖離する可能性がある。** ダッシュボードはDOWNを表示しているのに`recent_failures`が空のままという問題が発生しました。LambdaがDynamoDBの過去レコードをクエリしていたものの、現在の障害チェック結果をS3ペイロードに注入していなかったことが原因でした。解決策: 現在の障害チェック結果を直接`recent_failures`に書き込み、その後DynamoDBから過去の障害を取得し、`check_time`で重複排除して最新5件を保持します。

**読み取り専用ダッシュボードにはS3がAPI Gatewayより適している。** ファイル1つで、バックエンドなし、読み取りパスにコールドスタートなし。唯一のトレードオフはリアルタイム性です。ダッシュボードは最後のLambda実行時点の状態を反映します。

**個人プロジェクトでもIAMのスコープ設定は重要。** 権限を特定のARNに絞ることで、各サービスが実際に必要とする権限を明確に理解でき、その考え方はシステム設計の面接でも直接活かせます。

-----

## 今後の改善案

- 各サイトに`site_id`ルーティングを使ったマルチサイト監視
- サイトごとの稼働率およびインシデント数メトリクス
- ダッシュボードへのレスポンスタイムトレンドチャート追加（Chart.js）
- メールノイズ削減のための連続障害アラート閾値設定
- 古いレコードを自動削除するDynamoDB TTLの設定
- Lambdaの実行停止を検知するCloudWatchアラーム

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