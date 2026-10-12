# Calm Radio APIの調査記録

CRPが使っているCalm RadioのAPIについて、仕様、CRPでの使い方、調べ直す手順、これまでの経緯をまとめた開発者向けの文書です。

## この文書の位置づけ

- Calm RadioはAPIを一般に公開しておらず、公式の仕様書もありません。CRPは、Calm Radio運営元の許諾を得ずに非公式に開発しています。
- ここに書いた内容は、公式サイト（calmradio.com）の公開されているHTMLとJavaScript、APIのレスポンスを観察して得たものです。Calm Radio側の都合で、予告なく変わる可能性があります。
- 特に断りのない記述は、2026年10月10日から12日に確認した内容です。

## 経緯

| 時期 | 出来事 |
|---|---|
| 2017年7月 | Kodi用アドオン[nire0510/plugin.audio.calmradio](https://github.com/nire0510/plugin.audio.calmradio)の最終更新。`categories.json`、`channels.json`、`get_token`を使い、ストリームのURLに`ユーザー名:トークン@`を埋め込んで再生していた |
| 2022年2月～3月 | CRPの開発を開始。上記のアドオンを参考に、同じAPI（以下、v1）を使って実装した |
| 2022年3月14日 | v2のURL（`v2/metadata.json`、`v2/channels.json`）の存在に気付き、メモとして[Issue #1](https://github.com/actlaboratory/CRP/issues/1)を作成 |
| 2022年4月29日 | Version 1.0.0をリリース。v1を使用。マニュアルには、公式アプリはv2を使っていることと、CRPのv2への対応は技術的な理由で極めて困難であることを記載していた |
| 2026年10月10日 | チャンネル一覧が公式UIと違う原因を調査。v1は2018年以降更新されておらず、公式Webプレイヤーはv2を使っていることを確認した（調査結果は[Issue #1のコメント](https://github.com/actlaboratory/CRP/issues/1#issuecomment-6092041218)） |
| 2026年10月10日～12日 | v2に対応（[PR #3](https://github.com/actlaboratory/CRP/pull/3)、Version 1.1.0で公開予定）。変更したのはチャンネル一覧の取得だけで、ログイン（`get_token`）とストリームのURLの形式はv1のときのまま使えた |

## 現在使っているAPI（v2）

ベースURLは`https://api.calmradio.com/`です。

| 用途 | URL | 認証 |
|---|---|---|
| ジャンルとカテゴリー | `v2/metadata.json?locale=<言語>` | 不要 |
| チャンネル一覧 | `v2/channels.json?locale=<言語>` | 不要 |
| オーディオブックの章立て（CRPでは未使用） | `v2/stories.json` | 不要 |
| トークンの取得 | `get_token?user=<ユーザー名>&pass=<パスワード>` | ― |
| 再生中の曲の情報 | 各チャンネルの`recent_tracks`のURL | 不要 |

- `locale`には`en`や`ja`を指定します。`ja`を指定すると、チャンネル名、説明、ジャンル名、カテゴリー名が日本語訳で返ります。訳されていない項目は英語のままです。CRPは、アプリの言語設定（`ja-JP`なら`ja`）か、設定により`en`を指定しています。
- `get_token`はGETだけを受け付けます（POSTは404）。成功すると`{"membership": "active", "token": "..."}`の形で返り、`membership`が`active`ならプレミアム会員です。ユーザー名かパスワードが違う場合も200で、`{"error": "Invalid credentials"}`が返ります。

### `v2/metadata.json`

```json
{
    "metadata": {
        "rows": [ ... ],
        "categories": [ ... ]
    }
}
```

- `rows`：公式UIの最上位の分類です。
  - `kind`が`genre`のもの（7件）がジャンルです。`position`が表示順、`categories`が所属するカテゴリーIDの配列です。
  - そのほかの`kind`（`most_popular_all`、`more_to_discover`など）は「Most Popular Channels」などの特集の行です。CRPでは表示していません。
- `categories`：カテゴリーの配列です（43件）。`channels`が所属するチャンネルIDの配列で、`is_atmospheric`は環境音のカテゴリーかどうかを表します。
  - 「xxx」（id 54）はチャンネルが0件で、どのジャンルにも属していません。内部用と思われます。

### `v2/channels.json`

```json
{
    "channels": [ ... ]
}
```

チャンネルのフラットな配列です（776件）。CRPが使っている主な項目は次のとおりです。

| 項目 | 内容 |
|---|---|
| `id` | チャンネルID。`metadata.categories[].channels`から参照される |
| `title` | チャンネル名。前後に空白やタブが付いていることがあるため、CRPでは`strip()`している |
| `description` | 説明 |
| `vip` | 有料ストリームの配列。`vip[0]`が通常のストリームで、`vip[1]`以降は代替ストリーム。要素は`{"id", "recent_tracks", "streams": {"64", "192", "320"}}` |
| `free` | 無料ストリームの配列。空なら無料では再生できない。要素は`{"id", "recent_tracks", "streams": {"128"}}` |

CRPでは使っていない項目には、次のようなものがあります。

- `story`：オーディオブックのチャンネルかどうか
- `tunein_id`、`tunein_recent`、`force_tunein`：TuneIn経由の配信用
- `free_alexa`：Alexa向けの無料ストリーム
- 各種の画像URL（`square_art_url`など）

### ストリームのURL

- 形式は`https://streams.calmradio.com/api/<ストリームID>/<ビットレート>/stream`です。
- 有料ストリームは認証が必要です。CRPは`get_token`で取得したトークンを使い、`https://<ユーザー名>:<トークン>@streams.calmradio.com/...`の形でURLに埋め込んでいます。ユーザー名とトークンはURLエンコードします。
- 公式Webプレイヤーは、`?user=<ユーザー名>&pass=<トークン>`のクエリー文字列で渡しています。どちらの方式でも再生できます。
- 公式サイトの会員向けページからダウンロードできる再生URLのリスト（「VIP URLs AUTH1」）も、CRPと同じ形式のURLです。リストにはv1のチャンネル（562件）しか含まれていません。

## CRPでの使い方

`calmradio/main.py`の`getAllChannels()`で、次のようにツリーを組み立てています。

1. `metadata.rows`から`kind`が`genre`のものを取り出し、`position`の順に並べる。
2. 各ジャンルの`categories`のIDから`metadata.categories`を引き、さらに各カテゴリーの`channels`のIDから`channels`を引く。
3. チャンネルが0件のカテゴリーと、カテゴリーが0件のジャンルは表示しない。

再生するときは、プレミアム会員なら`vip[0].streams[<設定したビットレート>]`を、そうでなければ`free[0].streams["128"]`を使います。曲の情報は、使ったストリームの`recent_tracks`から取得します。

## APIを調べ直す手順

APIが変わってチャンネル一覧などが取得できなくなった場合は、次の手順で公式Webプレイヤーの実装を確認します。

1. `https://calmradio.com/en/`のHTMLを取得し、`<body>`の`data-channels-api-version`属性と`data-stories-api-version`属性を確認する。2026年10月時点では、どちらも`v2`。
2. HTMLが読み込んでいる`templates/calmradio/js/main.js`を取得し、`https://api.calmradio.com/`を含む文字列を検索する。`loadChannels`、`loadCategories`、`loadStories`という関数で、APIのURLを組み立てている。
3. ストリームのURLの組み立て方は、`main.js`の中で`streamUrl=`、`.vip`、`.free`を検索すると見つかる。
4. 見つけたURLのレスポンスを取得し、上の構造と比べる。

## 旧API（v1）

v1は2026年10月時点でも応答しますが、データは2018年から更新されていません。

| 用途 | URL |
|---|---|
| カテゴリー | `https://api.calmradio.com/categories.json` |
| チャンネル一覧 | `https://api.calmradio.com/channels.json` |

- `categories.json`は、「Channels」と「Atmospheres」の2つのグループの中に、計22のカテゴリーが入った入れ子の構造です。
- `channels.json`は、カテゴリーごとにチャンネルをまとめた配列です。チャンネル名には`CALMRADIO - `という接頭辞が付きます。
- ストリームは`streams`に入っています。有料ストリームは`"64"`、`"192"`、`"320"`、無料ストリームは`"free"`、`"free_128"`、`"free_56"`のキーです。無料ストリームがあるのは562件中261件です。CRPは以前、`"free_128"`を使っていました。
- 有料ストリームのURLはv2の`vip[0]`と、`"free_128"`のURLはv2の`free[0]`と同じです。
- v1のチャンネル（549件）は、すべてv2にも含まれています。

## 未対応の事項

- **オーディオブックの章立て**：公式Webプレイヤーは、`story`が`true`のチャンネルを`stories.json`の章立て用のストリーム（`.../story`）で再生し、章の移動ができるようにしています。CRPは通常のストリームを使っています。再生できることは確認済みですが、章の移動には対応していません。
- **特集の行**：「Most Popular Channels」などは表示していません。これらの行の`category`の値が何を指すかは、確認できていません。
