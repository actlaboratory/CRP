# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Calm Radio Player（CRP）は、インターネットラジオ「Calm Radio」を再生するWindows用のwxPythonアプリです。スクリーンリーダー利用者向けで、ACT Laboratoryの「GUI Application Kit」（`readme/GUI Application Kit.md`）をベースにしています。zipを展開して使うポータブル版として配布しています。

## コマンド

すべてリポジトリーのルートで実行します（`tools`に`cd`すると動きません）。

- 環境構築: `python -m pip install -r requirements.txt`
- 実行: `python crp.py`
- ビルド: `python tools\build.py`（PyInstallerで`dist\crp`に出力）
- 翻訳の抽出とマージ: `python tools\updateTranslation.py`（`locale/messages.po`と各言語の`.po`を更新）
- 翻訳のコンパイル: `python tools\buildTranslation.py`（`.mo`を生成）
- バージョンの更新: `python tools\bumpup.py [major|minor|patch]`

注意点:

- **32ビット版Python 3.12が必要です。** `crp.py`は64ビットのPythonでは起動せずに終了します。CI（`.github/workflows/testAndBuild.yml`）も`architecture: x86`でビルドしています。
- 自動テストやリンターはありません。動作確認は`docs/manual-test-scenario.txt`の手順で手動で行います。exeにしたときだけDLLやデータファイルが欠けて失敗することがあるため、ビルド関連の変更はビルドしたパッケージで確認します。
- masterへのプッシュでスナップショットがビルド・公開され、`*.*.*`のタグでリリースのドラフトが作られます。

## アーキテクチャー

起動の流れは`crp.py` → `app.Main`（`AppBase.MainBase`を継承した`wx.App`）です。`AppBase`がログ、設定、翻訳、スクリーンリーダー出力を初期化し、`app.Main.initialize()`が`Calmradio`、`Player`、`views.main.MainView`を生成します。アプリのインスタンスは`globalVars.app`に入り、各モジュールは`globalVars.app.config`や`globalVars.app.player`などを通じて共有の状態にアクセスします。

- `calmradio/`: Calm Radio APIの層。`api.py`はHTTP呼び出し、`main.py`は認証（`get_token`）とジャンル→カテゴリー→チャンネルの木構造の組み立て、再生URLの生成（URLに`ユーザー名:トークン@`を埋め込む）を担当します。APIは非公開・非公式で、仕様と経緯は`docs/calmradio-api.md`にまとめています。
- `player.py`: 外部パッケージ`soundPlayer`（BASSのラッパー）を包んだ再生制御。
- `nowPlayingChecker.py`と`playbackStatusChecker.py`: チャンネルを再生するたびに`views/main.py`の`Events.onChannelActivated`で作り直すデーモンスレッドです。UIの更新は必ず`wx.CallAfter`経由で行います。
- `views/`: wxのUI。`views/main.py`は`MainView`（コントロール）、`Menu`（メニュー構成）、`Events`（ハンドラー）の3クラス構成です。コントロールは`views/ViewCreator.py`で作ります。

### メニューとキー割り当て

メニュー項目を追加するときは、次の3か所をそろえます。

1. `menuItemsDic.py`: 参照名（例: `PLAY_STOP`）と表示文字列
2. `defaultKeymap.py`: 既定のショートカットキー（`mainView`、`HOTKEY`などのセクション）
3. `views/main.py`: `Menu.Apply`で登録し、`Events.OnMenuSelect`で処理

### 設定と翻訳

- 設定は`settings.ini`に保存します。既定値は`DefaultSettings.py`にあり、`ConfigManager`の`getint`、`getboolean`、`getstring`で既定値と範囲を指定して読みます。
- ポータブル版のため、設定をPCやWindowsアカウントに依存させてはいけません（DPAPI、資格情報マネージャー、レジストリーなどは不可）。パスワードも`settings.ini`に平文で保存しています。
- 翻訳はgettextです。**ソースの文字列は日本語**で`_("...")`で囲みます（`_`は`AppBase.InitTranslation`がビルトインに登録）。英語訳は`locale/en-us/LC_MESSAGES/messages.po`です。

### ログ

ログは`crp.log`に出力します。ロガーは`logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "モジュール名"))`の形で作ります。パスワード、トークン、それらを含むURLはログに残しません（`Api._getJson`の`sensitive`引数や、`Player.setPlaybackUrl`のマスク処理を参照）。

## コードと文書の規約

- インデントはファイルによって異なります（多くはタブ、`calmradio/`や`*Checker.py`は半角スペース4つ）。編集するファイルに合わせます。
- コメントは日本語で書きます。
- ユーザー向けの変更は`public/history.txt`の最新バージョンの項に追記します。`public/readme.txt`がユーザー向けのマニュアルです。
- `public/`のマニュアルは、JTFスタイルガイドよりもマニュアル内の既存の表記（「カテゴリ」「ユーザ」「フォルダ」など）との統一を優先します。
