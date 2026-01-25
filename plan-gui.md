# GUI対応

## 概要

* 現在の仕様はコマンドで全部の操作を行う、というもの。
* CUI操作のみでは使い勝手が悪いので、GUIでの操作も対応する。
* "画面構成"に記載しているように、抽出するファイル群とデータベース、LLMの設定を「プロジェクト」として管理し、CUIコマンド操作とその結果を各画面で表示できるようにする。
* フロントエンドとしてはローカルWeb UI(FastAPI + React/Vue)を採用

## 計画

* [x] tickets/done/260124-164005-gui-backend-scaffold.md
* [x] tickets/done/260124-164008-gui-project-model-storage.md
* [x] tickets/done/260124-164009-gui-api-data-endpoints.md
* [ ] tickets/260125-125901-api-provisional-regenerate.md
* [ ] tickets/260124-164011-gui-api-operations-runner.md
* [ ] tickets/260124-164013-gui-frontend-scaffold.md
* [ ] tickets/260124-164016-gui-frontend-projects-files.md
* [ ] tickets/260124-164017-gui-frontend-settings.md
* [ ] tickets/260124-164019-gui-frontend-terms-review.md

## 画面構成

### プロジェクト一覧（ホーム）

* 左：プロジェクト一覧（名前 / 最終更新 / ドキュメント数 / 用語数 / issues数）、一番下部に[新規作成]ボタン
* 右：選択プロジェクトの概要カード
  * 入力パス（target_docs相当）
  * LLM設定（provider/model）
  * 最終生成日時
  * ボタン：開く / 複製 / 削除

プロジェクトは、「登録したドキュメントを保存するファイル」+「プロジェクト専用DB」+「プロジェクト設定」をひとまとめにした“作業単位”

新規作成ボタンを押すと、プロジェクト名と使用するLLM設定を設定するウィンドウが表示され、プロジェクトが作成される

### プロジェクト詳細(メイン画面)

* レイアウトは 上からグローバル操作バー + 中央画面(左サイドバー + 右メイン画面) + ログビューで構成
* 右メイン画面は「上：操作バー」+「中：一覧＋詳細」の2段のレイアウト

#### グローバル操作バー

以下を表示

* 左寄せ
  * プロジェクト名
  * 状態バッチ(Up-to-date / Needs re-run / Running…)
* 右寄せ
  * ▶ 全実行
  * ■ 停止
  * 実行範囲ドロップダウン
    * Full
    * From Terms
    * Provisional→Refined など

#### 左サイドバー（ナビ）

* Files（登録文書）
* Terms（抽出用語）
* Provisional（暫定用語集）
* Issues（精査結果）
* Refined（最終用語集）
* Document Viewer（原文ビュー）
* Settings（設定）

Settings はプロジェクト全体の設定を行う画面で、プロジェクト名の変更や使用する LLM 設定の編集を行う。

選択すると、以降の右メイン画面を表示する

#### Files（登録文書）

* 上部:ボタン
  * ファイル追加/変更
  * 差分スキャン（追加・更新・削除の検出）
* 下部:文書一覧（パス / 更新日時 / 取り込み状態）
  * ダブルクリックで選択した文書のDocument Viewerへジャンプ
* 下部:詳細
  * ドキュメントの内容を表示

#### Terms（抽出用語）

* 上部：ボタン
  * 再抽出（terms regenerate）
  * 全削除 → 再抽出（CLIでやってるのと同じ概念）
* 下部：一覧（term / category / 出現回数 / 初出の文書）
* 下部：詳細
  * 出現箇所（文書名 + 行番号 + context）
  * ボタン：除外（exclude）/ 編集 / 手動追加

#### Provisional（暫定用語集）

* 上部:ボタン
  * 暫定用語集の再生成（provisional regenerate）
* 下部:一覧（term / definition / confidence）
* 下部:詳細
  * occurrences
  * 定義の編集（テキストエリア）
  * confidence調整（スライダでも数値でも）
  * ボタン：この用語を除外 / この用語だけ再生成（できるなら）

#### Issues（精査結果）

* 上部:ボタン
  * 精査結果の再生成
* 下部:一覧
  * issue_type でフィルタ（unclear / contradiction / missing）
* 下部:詳細
  * 問題説明

#### Refined（最終用語集）

* 上部:ボタン
  * 最終用語集の再生成
  * エクスポート：Markdown出力（export-md）
* 下部:一覧（term / definition / 出現箇所）

#### Document Viewer（原文ビュー）

* 上部:ボタン
  * 
* 下部:左:原文
  * タブで文書選択
  * クリックで用語選択
* 下部:右:用語カード
  * 定義（Refined）
  * 出現箇所一覧
  * 除外/編集/ジャンプボタン

#### Settings（設定）

左サイドバーからアクセスする、プロジェクト全体の設定を変更する画面。

以下の設定を変更する画面

* プロジェクト名
* LLM設定