---
link:
  - rel: 'stylesheet'
    href: 'countup.css'
---

# kumadeとは

## タスクランナー {#chap1_1}

日々の開発では同じような作業を何度もおこなう必要が出てきます。

たとえばコンパイルが必要な言語であればビルドの作業が何度も必要です。
単体テストやカバレッジの取得もコード変更のたびに実行するでしょう。

また、作業手順が複雑であったり作業間に依存関係があったりもします。

たとえばデプロイしようと思った場合、ビルドが済んでなければまずビルドが必要です。
そしてテストを実行して失敗していればデプロイを中断したいでしょう。
デプロイも複雑なコマンドを正しい順番で叩く必要があるかもしれません。

こういった何度もおこなう作業、複雑な作業を、逐一コマンドを叩いて実行していては大変です。
場合によっては間違ったコマンドを実行してしまう可能性もあります。
そこで自動化です。

自動化としてまず考えられるのは、shellスクリプトを書くことでしょう。
しかしshellスクリプトは少し複雑なことをやろうとすると途端に難しくなります。
また作業ごとにファイルを用意する必要も出てきますし、作業間の依存関係を解決するのも大変です。

そんなときに便利なのがタスクランナーです。

タスクランナーでは特定のファイルに作業をタスクとして書いておきます。
ファイルには複数のタスクを書くことができて、
各タスクで実行する処理内容だけでなく、タスク間の依存関係も指定できます。

そしてコマンドラインから特定のタスクをターゲットとしてタスクランナーを実行します。
するとタスクランナーは指定されたタスクが依存するタスクを芋づる式に洗い出し、
必要なタスクだけを正しい順序で実行してくれます。

kumadeもそんなタスクランナーの1つです。

有名なタスクランナーとしてGNU Make
<span class="footnote">https://www.gnu.org/software/make/</span>
やRubyで書かれたRake
<span class="footnote">https://docs.ruby-lang.org/ja/latest/library/rake.html</span>
などがあります。
これらはビルドで使われることが多いのでビルドツールとも呼ばれます。
しかし、たとえばテスト実行やインストールといったビルド以外の作業にも使われているので、
タスクランナーと呼ぶのがふさわしいでしょう。

## kumadeの特徴 {#chap1_2}

kumadeはPythonで書かれたタスクランナーで、次のような特徴があります：

- `Kumadefile.py`にPythonのコードでタスクを定義できます
- `kumade`コマンドで指定したタスクを実行できます
- タスクは依存関係を考慮して必要なものだけが正しい順序で実行されます
- ファイルを生成するタスクの場合、ファイルの存在やタイムスタンプも考慮されます

Pythonでタスクを定義できるので、Pythonを使っている環境での導入が容易です
（Rakeも素晴らしいツールなのですが、Rubyを使っていない環境では導入しづらいです）。

また、最後の特徴はビルドやデータ分析でとても役立つものです。

たとえばデータ分析では複数のファイルをダウンロードしてきて前処理を掛けることが考えられます。
このとき、すでにダウンロードしてあるファイルを再びダウンロードするのは無駄ですし、
前処理も入力ファイルより出力ファイルの方が新しければ不要です。
kumadeではファイルの存在やタイムスタンプが考慮されるので、
これらの不要な処理は自動でスキップされます。

## 名前の由来 {.column #column1}

kumadeという名前は影響を受けたRakeが熊手を意味するところからつけました。
熊手は縁起物ですし、“made”とMakeを連想させる文字列も含まれているので、ちょうどいいかなと。
PythonのテンプレートエンジンであるJinjaがTemplate→Temple→Jinjaという連想で名付けられたのと
同じようなものですね。
