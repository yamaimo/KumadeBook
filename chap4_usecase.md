---
link:
  - rel: 'stylesheet'
    href: 'countup.css'
---

# kumadeの活用例

## 組版のビルド自動化 {#chap4_1}

この章ではkumadeの活用例として組版のビルド自動化を紹介します。

本書もそうですが、書籍を作るときには文章や図表をレイアウトして
紙面を構成する必要があります。
この作業のことを組版といいます。

組版のためのソフトはいろいろあるのですが、本書の制作ではその1つであるVivliostyle
<span class="footnote">https://vivliostyle.org/</span>
を使っています。
Vivliostyleでは原稿をMarkdownやHTMLで書き、CSSでデザインを調整します。
そのためCUIベースで作業を進められるのでバージョン管理もしやすいです。
またCSSでデザインするので凝ったデザインも比較的容易に作れます。
書籍<span class="footnote">『Web技術で「本」が作れるCSS組版Vivliostyle入門』</span>
も出ているので、気になった人は読んでみてください。

さて、そんなVivliostyleですが、使ってみると2つほど困ったことがありました。

- 改行で半角スペースが入ってしまう
- 複数バリアントを出力できない

まず1つ目「改行で半角スペースが入ってしまう」です。

原稿をMarkdownで書いていると、文や段落の途中であっても
適当に改行を入れて1行の幅をある程度で抑えたくなります。
しかし、MarkdownがHTMLに変換されるときにこの改行がそのまま残ってしまうので、
HTMLの仕様上、改行した位置に半角スペースが挿入され、
文や段落の途中に不自然な空きが生じてしまいます。
これを防ぐには段落の中で改行しないようにするしかないのですが、
それではとても不便です。

そして2つ目「複数バリアントを出力できない」です。

書籍を紙でも電子でも頒布する場合、電子書籍として頒布するPDFと
印刷所に回して印刷するPDFをそれぞれ用意する必要があります。
これらは入力の原稿自体は同じなのですが、出力要件が微妙に異なります：

- 電子版
    - 画像はカラー
    - 表紙、裏表紙のページも追加する
    - トンボは不要
- 印刷版
    - 画像はグレースケール
    - 表紙、裏表紙は不要（別のデータで入稿する）
    - トンボが必要

そのため、設定を変えた出力（すなわちバリアントの出力）が必要なのですが、
現状では複数バリアントの出力に対応していません。

これらの問題に対処するにはビルド方法を工夫する必要があります。
ただし工夫するとビルド手順は複雑になるので、それをkumadeで自動化してみます。

## Markdownの前処理 {#chap4_2}

まず「改行で半角スペースが入ってしまう」問題への対処です。

これに対しては、原稿のMarkdownに対してPythonで前処理をかけ、
文や段落の途中に入っている不要な改行を取り除くようにしました。

基本的には原稿を1行ずつ読み込み、行末の改行を取り除いて出力します。
ただし改行を取り除いてはいけないケースもあります：

- フロントマター
<span class="footnote">ファイル先頭で`---`行と`---`行の間にYAMLでメタデータを記述できる。</span>内
- コードブロック内
- 箇条書きの直前
- ？や！で終わる場合
- 空行自身

状態遷移として整理すると次のようになります：

![前処理の状態遷移](images/pp_state.png)

これをStateパターンで書いたのが次のPythonコードです：

```python title=preprocess.py
import re
from pathlib import Path
from typing import Protocol, TextIO

FRONT_MATTER_FENCE = re.compile(r"^---")
CODE_BLOCK_FENCE = re.compile(r"^```")
ITEMIZE_BEGIN = re.compile(r"^\s*([0-9]+.|[\-+*])\s+")
EMPTY_LINE = re.compile(r"^$")
LF_SYMBOLS = re.compile(r"[？！]$")

class ProcessorState(Protocol):
    def process_line(self, line: str, outfile: TextIO) -> "ProcessorState":
        ...

class InitState(ProcessorState):
    def process_line(self, line: str, outfile: TextIO) -> ProcessorState:
        if FRONT_MATTER_FENCE.search(line):
            outfile.write(line)
            return InFrontMatter()
        else:
            return NormalState().process_line(line, outfile)

class InFrontMatter(ProcessorState):
    def process_line(self, line: str, outfile: TextIO) -> ProcessorState:
        outfile.write(line)
        if FRONT_MATTER_FENCE.search(line):
            return NormalState()
        else:
            return self

class InCodeBlock(ProcessorState):
    def process_line(self, line: str, outfile: TextIO) -> ProcessorState:
        outfile.write(line)
        if CODE_BLOCK_FENCE.search(line):
            return NormalState()
        else:
            return self

class NormalState(ProcessorState):
    def process_line(self, line: str, outfile: TextIO) -> ProcessorState:
        if CODE_BLOCK_FENCE.search(line):
            outfile.write(line)
            return InCodeBlock()
        elif EMPTY_LINE.search(line) or LF_SYMBOLS.search(line):
            outfile.write(line)
            return self
        else:
            outfile.write(line.rstrip())
            return DelayLineFeedState()

class DelayLineFeedState(ProcessorState):
    def process_line(self, line: str, outfile: TextIO) -> ProcessorState:
        if CODE_BLOCK_FENCE.search(line):
            outfile.write("\n")
            outfile.write(line)
            return InCodeBlock()
        elif EMPTY_LINE.search(line) or ITEMIZE_BEGIN.search(line):
            outfile.write("\n")
            return NormalState().process_line(line, outfile)
        elif LF_SYMBOLS.search(line):
            outfile.write(line)
            return NormalState()
        else:
            outfile.write(line.rstrip())
            return self

def preprocess(inpath: Path, outpath: Path) -> None:
    with inpath.open() as infile:
        with outpath.open("w") as outfile:
            state: ProcessorState = InitState()
            for line in infile:
                state = state.process_line(line, outfile)
```

各クラスはそれぞれの状態
（初期状態 / フロントマター内 / コードブロック内 / 通常状態 / 改行遅延状態）を表していて、
入力で読み込んだ1行を`process_line()`メソッドで処理して次の状態を返します。

## ディレクトリ構成 {#chap4_3}

次に「複数バリアントを出力できない」問題への対処です。

これに対しては、ビルドするディレクトリをバリアントごとに分けるようにしました。
各ディレクトリにそのバリアントで必要となるファイルをコピーしてビルドすることで、
それぞれのディレクトリで異なった出力が得られるようになります。

ディレクトリの全体像は次のようになります：

```
- KumadeBook/
    - build_ebook/          電子用のビルドディレクトリ（バージョン管理外）
    - build_print/          印刷用のビルドディレクトリ（バージョン管理外）
    - theme/                デザインのCSS（テーマ）のあるディレクトリ
    - assets_ebook/         電子用のアセット
        - vivliostyle.config.js     電子用の設定
        - images/           電子用の画像（カラー）
    - assets_print/         印刷用のアセット
        - vivliostyle.config.js     印刷用の設定
        - images/           印刷用の画像（グレースケール）
    - Kumadefile.py         Kumadefile
    - preprocess.py         Markdown前処理のスクリプト
    - package.json          パッケージの設定
    - package-lock.json     パッケージの設定（固定用）
    - *.md                  原稿のMarkdown
    - *.css                 デザイン調整用のCSS
```

テーマのディレクトリは以下のようになっています：

```
- KumadeBook/
    - theme/
        - package.json      パッケージの設定
        - package-lock.json パッケージの設定（固定用）
        - node_modules/     依存するパッケージ（バージョン管理外）
        - scss/
            - *.scss        ソースとなるSCSS
        - theme_ebook.css   変換後の電子用CSS（バージョン管理外）
        - theme_print.css   変換後の印刷用CSS（バージョン管理外）
```

デザインは表現力の高いSCSSで書き、CSSに変換して使っています。

ビルドディレクトリは以下のようになります：

```
- KumadeBook/
    - build_ebook/
        - KumadeBook.ebook.pdf  出力されるPDF
        - package.json          パッケージの設定（コピー）
        - package-lock.json     パッケージの設定（固定用）（コピー）
        - node_modules/         依存するパッケージ（バージョン管理外）
        - theme/
            - theme_ebook.css   デザインのCSS（コピー）
        - images/               画像（コピー）
        - vivliostyle.config.js 設定（コピー）
        - *.md                  前処理後のMarkdown（preprocessで出力）
        - *.html                変換後のHTML
        - *.css                 デザイン調整用のCSS（コピー）
```

見ての通り、必要なファイルを前処理やコピーしてきてビルドすることになります。
すると、同じファイルを何度もコピーするのは無駄なので、
更新の必要なファイルだけコピーするのが望ましいです。
また、テーマのCSSはコピーする前に存在しなければSCSSからの変換が必要ですし、
あるいはSCSSに更新があった場合にもCSSへの変換やビルドディレクトリへのコピーが必要になります。

こういった複雑な処理を手動でやっていては大変です。
そこでkumadeの出番となります。

## ビルドのタスク定義 {#chap4_4}

それではビルドの各処理をKumadefile.pyにタスクとして定義していきます。

### ライブラリのインポート、基本的な設定

まずはライブラリをインポートし、基本的なことを設定します。

```python title=Kumadefile.py（ライブラリのインポート、基本的な設定）
import kumade as ku

import shutil
import subprocess
import sys
from pathlib import Path

project_dir = Path(__file__).parent

# preprocess.pyをロードできるようにする
sys.path.append(str(project_dir))
from preprocess import preprocess

ku.set_default("build")

# ebook: 電子用, print: 印刷用
variants = ["ebook", "print"]
```

ここではバリアントとして電子用と印刷用を用意しようとしています。

### ファイルの設定

次にファイルの設定です。

原稿となるMarkdownファイルの一覧を用意したり、
ビルドディレクトリ、アセットディレクトリなどのパスを設定します。

```python title=Kumadefile.py（ファイルの設定）
# Files ----------

md_files = [
    "cover1.md",
    "opening.md",
    "toc.md",
    "chap1_intro.md",
    "chap2_getstart.md",
    "chap3_kumadefile.md",
    "chap4_usecase.md",
    "closing.md",
    "cover4.md",
]

json_files = ["package.json", "package-lock.json"]

css_files = ["countup.css", "reset_page.css"]

theme_dir = project_dir / "theme"

build_dir = {}
pdf_path = {}
theme_css_path = {}
assets_dir = {}
assets_paths: dict[str, list[Path]] = {}
pp_md_paths: dict[str, list[Path]] = {}
for variant in variants:
    build_dir[variant] = project_dir / f"build_{variant}"
    pdf_path[variant] = build_dir[variant] / f"KumadeBook.{variant}.pdf"
    theme_css_path[variant] = theme_dir / f"theme_{variant}.css"
    assets_dir[variant] = project_dir / f"assets_{variant}"
    assets_paths[variant] = []  # あとで追加していく
    pp_md_paths[variant] = []  # あとで追加していく
```

ビルドディレクトリやアセットディレクトリはバリアントごとに異なるので、
バリアントをキーとした辞書にしています。

### ビルドディレクトリの初期化

ここから具体的なタスクを定義していきます。

まずはビルドディレクトリの初期化です。

```python title=Kumadefile.py（ビルドディレクトリの初期化）
# Initialize build directory ----------

for variant in variants:
    ku.directory(build_dir[variant])

    depend_paths = []
    for json_file in json_files:
        src_json = project_dir / json_file
        dst_json = build_dir[variant] / json_file
        depend_paths.append(dst_json)

        @ku.file(dst_json)
        @ku.depend(build_dir[variant], src_json)
        @ku.bind_args(src_json, dst_json)
        def copy_json(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    node_modules_dir = build_dir[variant] / "node_modules"

    @ku.file(node_modules_dir)
    @ku.depend(*depend_paths)
    @ku.bind_args(build_dir[variant])
    def install_dependencies(work_dir: Path) -> None:
        subprocess.run(["npm", "install"], cwd=work_dir)

    @ku.task(f"init_build_{variant}")
    @ku.help(f"Initialize build directory for {variant}.")
    @ku.depend(node_modules_dir)
    def init_build_dir() -> None:
        pass
```

各バリアントでタスクを作っています。
ループでタスクを定義できるのが便利です。

まず`ku.directory(build_dir[variant])`でディレクトリ生成タスクを定義しています。

そしてビルドディレクトリではパッケージの設定と依存パッケージのインストールが必要です。
そこでパッケージの設定が書かれたJSONファイルをコピーしてくるタスクと、
そのコピーしてきたJSONファイルを使って依存パッケージをインストールするタスクを定義しています。
依存パッケージのインストールはコピーされたJSONに依存しますし、
コピーされたJSONはコピー元のJSON、それとビルドディレクトリの存在に依存するので、
それぞれ適切に依存関係を追加しています。

ここで、タスク定義をするときに`@ku.bind_args()`デコレータを使っていることに注意してください。
これはループの中でタスクを定義しているので、
タスクを定義した時点で変数が指しているオブジェクトをタスクに束縛しておく必要があるためです。

最後に`init_build_ebook`および`init_build_print`という通常タスクを定義しています。
これらを実行すると、依存関係を辿ってビルドディレクトリの作成、
パッケージ設定のコピー、依存パッケージのインストールが、必要に応じて実行されます。

### アセットのコピー

次は設定や画像といったアセットのコピーです。
テーマのCSSなどもコピーします。

```python title=Kumadefile.py（アセットのコピー）
# Copy assets ----------

for variant in variants:
    src_config = assets_dir[variant] / "vivliostyle.config.js"
    dst_config = build_dir[variant] / "vivliostyle.config.js"
    assets_paths[variant].append(dst_config)

    @ku.file(dst_config)
    @ku.depend(build_dir[variant], src_config)
    @ku.bind_args(src_config, dst_config)
    def copy_config(src: Path, dst: Path) -> None:
        shutil.copy(src, dst)

    build_image_dir = build_dir[variant] / "images"
    ku.directory(build_image_dir)

    for src_image in (assets_dir[variant] / "images").iterdir():
        dst_image = build_image_dir / src_image.name
        assets_paths[variant].append(dst_image)

        @ku.file(dst_image)
        @ku.depend(build_image_dir, src_image)
        @ku.bind_args(src_image, dst_image)
        def copy_image(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    for css_file in css_files:
        src_css = project_dir / css_file
        dst_css = build_dir[variant] / css_file
        assets_paths[variant].append(dst_css)

        @ku.file(dst_css)
        @ku.depend(build_dir[variant], src_css)
        @ku.bind_args(src_css, dst_css)
        def copy_css(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    build_theme_dir = build_dir[variant] / "theme"
    ku.directory(build_theme_dir)

    dst_theme_css = build_theme_dir / theme_css_path[variant].name
    assets_paths[variant].append(dst_theme_css)

    @ku.file(dst_theme_css)
    @ku.depend(build_theme_dir, theme_css_path[variant])
    @ku.bind_args(theme_css_path[variant], dst_theme_css)
    def copy_theme_css(src: Path, dst: Path) -> None:
        shutil.copy(src, dst)

    @ku.task(f"copy_assets_{variant}")
    @ku.help(f"Copy assets for {variant}.")
    @ku.depend(*assets_paths[variant])
    def copy_assets() -> None:
        pass
```

ファイルをビルドディレクトリにコピーしてきていますが、
ビルドディレクトリの初期化でファイルをコピーしているのと同様です。

一つ補足すると、PDFの出力はこういったアセットに依存しているので、
あとで依存関係を指定できるように、ループを回しながら`assets_paths[variant]`に
アセットのパスを追加しています。

### Markdown原稿の前処理

Markdownの原稿はただ単にコピーするのではなく`preprocess()`関数で前処理します。

```python title=Kumadefile.py（Markdown原稿の前処理）
# Preprocess sources ----------

for variant in variants:
    for md_file in md_files:
        md_path = project_dir / md_file
        pp_md_path = build_dir[variant] / md_file
        pp_md_paths[variant].append(pp_md_path)

        @ku.file(pp_md_path)
        @ku.depend(build_dir[variant], md_path)
        @ku.bind_args(md_path, pp_md_path)
        def preprocess_md(src: Path, dst: Path) -> None:
            preprocess(src, dst)

    @ku.task(f"pp_md_{variant}")
    @ku.help(f"Preprocess sources for {variant}.")
    @ku.depend(*pp_md_paths[variant])
    def preprocess_sources() -> None:
        pass
```

前処理済みのMarkdownもPDF出力の依存関係で指定する必要があるので、
ループを回しながら`pp_md_paths[variant]`にパスを追加しています。

### PDFのビルド

PDFをビルドするタスクを定義します。

```python title=Kumadefile.py（PDFのビルド）
# Build PDF ----------

for variant in variants:
    @ku.task(f"build_{variant}")
    @ku.help(f"Build PDF for {variant}.")
    @ku.depend(pdf_path[variant])
    def build() -> None:
        pass

    depend_paths = [*assets_paths[variant], *pp_md_paths[variant]]

    @ku.file(pdf_path[variant])
    @ku.depend(f"init_build_{variant}", *depend_paths)
    @ku.bind_args(build_dir[variant])
    def build_pdf(work_dir: Path) -> None:
        subprocess.run(["npm", "run", "build"], cwd=work_dir)

build_tasks = [f"build_{variant}" for variant in variants]

@ku.task("build")
@ku.help(f"Build all PDFs.")
@ku.depend(*build_tasks)
def build_all() -> None:
    pass
```

出力するPDFはアセットや前処理済みのMarkdownに依存するので依存関係を追加しています。

そして各バリアントのPDFをビルドするタスクを
`build_ebook`および`build_print`として定義しています。

それに加えて両方のバリアントをビルドするタスクを`build`として定義しています。
これは冒頭で`ku.set_default("build")`としているのでデフォルトのタスクでもあります。

### テーマのビルド

あとはテーマのCSSのビルドです。

```python title=Kumadefile.py（テーマのビルド）
# Build Theme ----------

theme_node_modules_dir = theme_dir / "node_modules"
scss_dir = theme_dir / "scss"
scss_paths = list(scss_dir.glob("*.scss"))
theme_built_path = theme_dir / "theme_built"

@ku.file(theme_node_modules_dir)
def install_theme_dependencies() -> None:
    subprocess.run(["npm", "install"], cwd=theme_dir)

for variant in variants:
    @ku.file(theme_css_path[variant])
    @ku.depend(theme_built_path)
    def create_css() -> None:
        pass

@ku.file(theme_built_path)
@ku.depend(theme_node_modules_dir, *scss_paths)
def build_theme() -> None:
    subprocess.run(["npm", "run", "build"], cwd=theme_dir)
    theme_built_path.touch()
```

テーマをビルドするにはその前に依存するパッケージをインストールしておく
必要があります。

そしてテーマのCSSはSCSSのソースから変換して作るのですが、
この出力は電子用と印刷用の複数の出力があります。
そこで3章のトピックで説明したとおり、
タイムスタンプを記録するダミーのファイルを介して依存関係を結ぶようにしています。

### その他のタスク定義

これでビルドに必要なタスク定義は一通り終わったのですが、
追加でいくつかのタスクを定義しておきます。

```python title=Kumadefile.py（その他のタスク定義）
# Open PDF (for mac) ----------

for variant in variants:
    @ku.task(f"open_{variant}")
    @ku.help(f"Open PDF for {variant}.")
    @ku.depend(f"build_{variant}")
    @ku.bind_args(pdf_path[variant])
    def open_pdf(path: Path) -> None:
        subprocess.run(["open", str(path)])


# Delete outputs ----------

output_paths = list(build_dir.values())

ku.clean("clean", output_paths, help="Delete outputs.")
```

まずはビルドしたPDFをプレビューで開くタスクです。
これはそれぞれ`open_ebook`、`open_print`として定義しています。
これでビルド結果を簡単に確認できます
（ビルドがまだなら先にビルドが実行されます）。

また、ビルドディレクトリを削除する`clean`というタスクも定義しています。

### タスクの確認

最後にタスク一覧を確認してみます：

```console
$ kumade -t
build              # Build all PDFs.
build_ebook        # Build PDF for ebook.
build_print        # Build PDF for print.
clean              # Delete outputs.
copy_assets_ebook  # Copy assets for ebook.
copy_assets_print  # Copy assets for print.
init_build_ebook   # Initialize build directory for ebook.
init_build_print   # Initialize build directory for print.
open_ebook         # Open PDF for ebook.
open_print         # Open PDF for print.
pp_md_ebook        # Preprocess sources for ebook.
pp_md_print        # Preprocess sources for print.
```

これらがKumadefile.pyで定義された（そして説明がつけられた）タスクです。

たとえば両方のバリアントのPDFをビルドする場合、`kumade build`コマンドを実行します。
これはデフォルトのタスクなので単に`kumade`コマンドでもOKです。
あるいは電子用のPDFをビルドしてプレビューを見る場合、
`kumade open_ebook`コマンドを実行します。

実際に試してみると、kumadeが必要なタスクだけを正しい順番で実行するのが分かるかと思います。
このように、ビルドのような複雑な処理も、kumadeを使えば簡単に実行できるようになります。

## 同人誌紹介（その3） {.column}

### Math Poker Girl

![](images/MathPokerGirl.png)

https://imoarai.booth.pm/items/1558968

ポーカー（テキサス・ホールデム）について数学的に考察する本です。
ルールの説明もあります。
世に出回ってるフワッとした言説の真実を数学の力で暴きます。

### コウモリ少女に恋してる 数理最適化入門

![](images/OptGirl.png)

https://imoarai.booth.pm/items/1873654

数理最適化の入門書です。
物語を通して数理最適化の概要と線形計画問題について学びます。
モデリング、理論、アルゴリズム、ソルバーの利用と、幅広い内容を知ることができます。

### 不確実な世界で意思決定する技術

![](images/StochasticOpt.png)

https://imoarai.booth.pm/items/2397832

不確実性のある最適化問題を扱った本です。
実務で数理最適化を使おうとすると不確実性の問題は避けて通れません。
それに対する手段の一つとして確率計画法を説明しています。
