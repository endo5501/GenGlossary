重大：@gui-plan.md で記載された仕様と現在の実装をよく見比べるべき

* 最初に表示される、プロジェクト一覧（ホーム）の仕様が @gui-plan.md と大きく異なる
* Create画面
  * ユーザにDocument Rootを決めさせるのは適切ではない。現在の./project/以下にプロジェクトのディレクトリを自動で作るべき
  * LLM Providerは現在ollamaとopenaiを選択できるが、テキスト入力なのは不適切。ドロップダウンメニューにすべき
  * openaiを選択した時、URLなどを選択できるべき
* Files,Terms,Provisional,Issues,Refined,Document Viewer,Settings 
  * 選択しても何も表示されない
  * プロジェクト一覧に戻れない
