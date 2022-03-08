[![Test](https://github.com/mypaceshun/opime-notify/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/mypaceshun/opime-notify/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/mypaceshun/opime-notify/branch/main/graph/badge.svg?token=Y6MD6SC48H)](https://codecov.io/gh/mypaceshun/opime-notify)
# opime-notify
推しごと支援ツール for opime

LINE Messaging API を利用した通知botです。
Googleスプレッドシートに記録した通知リストをチェックし、
適切なタイミングでLINE通知botに通知を飛ばします。

# Usage

現在は以下のbotへ通知を飛ばすように動作しています。

* おぴめ通知bot https://lin.ee/U48L316

# for developer

当プログラムの利用には以下が必要です。

* Python >= 3.9
* Poetry

またLINE Messaging API を利用しているのでその事前準備をし、通知を飛ばしたいチャンネルのアクセストークンを取得してください。

* https://developers.line.biz/ja/docs/messaging-api/overview/

通知リストはGoogleスプレッドシートから取得するようになっています。
Googleスプレッドシートにアクセスできるように Google Sheets API の準備をし、アクセス用のJSONキーと取得先スプレッドシートのIDを取得してください。
[`gspread`](https://docs.gspread.org/en/latest/index.html)というライブラリを利用しているので、ドキュメントを参考に必要なデータを取得してください。

* https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

## スプレッドシートの準備

スプレッドシートのヘッダー部(1行目)は自身で作成する必要があります。
プログラム実行前に以下の内容を各行に記載しておいてください。

```
id | title | date | description | url | status
```

それぞれの行の説明は以下です。

* id

  通知ID。
  現状利用していません。

* title

  通知のタイトルに利用される文字列です。

* date

  通知されるタイミングです。
  YYYY/dd/mm HH:MM:SS の形式で記載してください。

* description

  通知の本文になります。

* url

  通知の末尾に付属するURLです。通知内容に関連したサイトのリンクを設定します。

* status

  基本的には空欄で問題ありません。
  何かしらの原因で通知に失敗した際に、エラーメッセージが記録されます。

# command

## opime-notiry

メインとなるコマンドです。
指定のGoogleスプレッドシートから通知リストを取得し、LINEの通知用botへ通知を送信します。

Poetry を利用した実行手順は以下のとおりです。

```
$ poetry install --no-dev
$ poetry run opime-notify
```

コマンドにはいくつかの引数を設定できます。
`--google-json-key`や`--line-access-token`を指定しないと、それぞれのAPIへのアクセスに失敗します。

```
Usage: opime-notify [OPTIONS]

Options:
  --line-access-token TEXT  line access token
  --gsheet-id TEXT          cache spread sheet id
  --google-json-key PATH    google json key file
  --help                    Show this message and exit.
```

引数は環境変数で設定することも可能です。
また `python-dotenv` を利用し、 `.env` というファイル名で記載された環境変数の設定を読めるようになっています。
以下のような `.env` ファイルを作成することで、引数なしでプログラムを実行することが可能です。

* `.env`
```
LINE_ACCESS_TOKEN=xxxxxxx
GOOGLE_JSON_KEY_FILE=~/secret/google-key.json
GSHEET_ID=xxxxxx
```
