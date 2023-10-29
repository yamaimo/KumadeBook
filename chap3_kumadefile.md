---
link:
  - rel: 'stylesheet'
    href: 'countup.css'
---

# Kumadefileの書き方

## 基本 {#chap3_1}

`Kumadefile.py`では以下のようにタスクを定義します。

```python title=タスク定義の例
import kumade as ku

# 通常のタスク定義

@ku.task(<タスク名>)
...  # その他のデコレータ
def do_something() -> None:
    ...  # タスクで実行する処理

# ファイル生成タスクの定義

@ku.file(<ファイルのパス>)
...  # その他のデコレータ
def create_file() -> None:
    ...  # ファイルを生成する処理
```

まず必要なのはライブラリのインポートで、ここでは`ku`としてインポートしています。

通常のタスクを定義する場合、`@kumade.task(name: str)`デコレータを使います。
タスク名は文字列で指定します。
そしてタスクで実行する内容を関数に書きます。

ファイル生成タスクを定義する場合、`@kumade.file(path: Path)`デコレータを使います。
ファイルのパスは`pathlib.Path`のオブジェクトで指定します。
文字列では指定できないので注意してください。
そしてファイルを生成する処理を関数に書きます。

通常のタスクは依存するタスクをすべて実行したあとに常に実行されます。

一方でファイル生成タスクの場合、依存するタスクをすべて実行したあとで、
生成するファイルがまだ存在しないか、依存するファイルよりも古いときのみ
タスクは実行されます。
これにより無駄な処理は実行されなくなります。

`Kumadefile.py`の中でタスクは何個でも定義できます。
タスクの定義順は自由です。
たとえば依存されるタスクを依存するタスクよりもあとで定義することもできます。
kumadeはタスクの定義順ではなく依存関係から適切な実行順を求めてタスクを実行します。

デフォルトのタスクを指定したい場合、`kumade.set_default(name: str)`関数を使います。
`kumade`コマンドでターゲットを指定せずに実行した場合、この関数で指定されたタスクが実行されます。

## 各種デコレータ {#chap3_2}

タスクの定義にはデコレータでタスクの説明や依存関係を追加できます。

### タスクの説明

タスクに説明を追加したい場合、`@kumade.help(desc: Optional[str])`デコレータを使います。
`desc`に指定した文字列がこのタスクの説明になります。
ファイル生成タスクには使えないので注意してください。

```python title=タスクの説明の追加
@ku.task("build")
@ku.help("Build something.")
def build() -> None:
    ...
```

説明が追加されたタスクは`kumade -t`コマンドで一覧に表示されます。

```console
$ kumade -t
build  # Build something.
...
```

### 依存するタスク

依存するタスクを指定するには`@kumade.depend(*dependencies: Optional[TaskName])`
デコレータを使います。
依存するタスクをタスク名もしくはファイルのパスで任意個指定します。

```python title=依存するタスクの指定
@ku.task("deploy")
@ku.depend("test", "setup_server", config_file)
def deploy() -> None:
    ...
```

このタスクは依存するタスクがすべて終わってから実行されるようになります。

なお、依存するタスクは列挙した順に実行されるとは限らないことに注意してください。
もし列挙したタスク間にも依存関係があるのであれば、
それらのタスクで依存関係を別途指定してください。

### オブジェクトの束縛

Pythonでは関数外の変数を参照した場合、変数の値ではなく変数そのものが関数に束縛されます。
そして、その変数がどのオブジェクトを指しているのかは、関数の実行時に解決されます：

```python title=関数での変数の束縛
x = 1
def show_x() -> None:
    print(x)  # 1という値ではなくxという変数が束縛される

show_x()  # => 1が表示される

x = 2
show_x()  # => 1ではなく2が表示される
```

これはループを使ってタスクを定義したい場合に問題になります：

```python title=ループ内でのタスク定義（問題があるバージョン）
for i in range(5):
    @ku.task(f"task{i}")
    def show_i() -> None:
        print(i)

# task0では0が表示されてほしいが、実際には4が表示されてしまう
# task1 ~ task3も同様
```

この問題を解決するには`@kumade.bind_args(*args: Any)`デコレータを使います。
このデコレータで指定されたオブジェクトはタスクに束縛され、
タスク実行時に関数に引数として渡されます：

```python title=ループ内でのタスク定義（問題がないバージョン）
for i in range(5):
    @ku.task(f"task{i}")
    @ku.bind_args(i)        # タスク定義時点のiの値を束縛する
    def show_i(i: int) -> None:  # 束縛された値を引数で受け取る
        print(i)

# task0では0, task1では1, ...が表示されるようになる
```

具体的な使用例は4章で見ていきます。

## その他のトピック {#chap3_3}

### ディレクトリ生成タスク

ディレクトリを作成するタスクを定義したい場合、
`kumade.directory(path: Path, dependencies: Optional[List[TaskName]] = None)`
関数を使ってください。

```python title=ディレクトリ生成タスクの定義
build_dir = Path("build")
ku.directory(build_dir)
```

ディレクトリ生成タスクは指定されたディレクトリが存在しない場合に
そのディレクトリを作成します。
親ディレクトリが存在しない場合は親ディレクトリも作成します。

### ファイル削除タスク

生成されたファイルを削除するタスクを定義したい場合、
`kumade.clean(name: str, paths: List[Path], dependencies: Optional[List[TaskName]] = None, help: Optional[str] = None)`
関数を使ってください。
`name`はタスク名、`paths`は削除したいファイルのパスのリストです。

```python title=ファイル削除タスクの定義
clean_paths = [Path("build.log"), Path("build")]
ku.clean("clean", clean_paths, help="Clean output.")
```

ファイル削除タスクは指定された一連のファイルを削除します。
ファイルのパスがディレクトリの場合、中に含まれるファイルも削除されます。

### ファイル操作、コマンド実行

作業でファイルを操作したい場合、標準ライブラリの`pathlib`や`shutil`が便利です。
詳細はドキュメントを参照してください。

- pathlib: https://docs.python.org/3/library/pathlib.html
- shutil: https://docs.python.org/3/library/shutil.html

また、コマンドを実行したい場合、標準ライブラリの`subprocess`が使えます。
標準入出力としてファイルを渡したり、コマンドの終了コードを確認することもできます。
詳細はドキュメントを参照してください。

- subprocess: https://docs.python.org/3/library/subprocess.html

### 複数ファイル出力への対応

1つのタスクで複数のファイルを出力することがあります。
この場合、どのファイル生成タスクに処理を書いたらいいのかという問題があります：

```python title=複数のファイルを出力する場合の問題
# CSVが入力
input_files = list(Path("input_dir").glob("*.csv"))

# 入力から集計とグラフを出力
summary = Path("summary.csv")
graph = Path("graph.png")

@ku.file(summary)
@ku.depend(*input_files)
def output_summary() -> None:
    ...  # ここで出力処理を書く？

@ku.file(graph)
@ku.depend(*input_files)
def output_graph() -> None:
    ...  # それともここで出力処理を書く？
```

こういったときにはタイムスタンプを記録するダミーのファイルを用意し、
ダミーファイルを仲介する形でタスクを定義します：

```python title=複数ファイル出力への対応
# 入力と出力のファイル定義は省略

# タイムスタンプを記録するファイル
built_path = Path("built")

@ku.file(summary)
@ku.depend(built_path)
def output_summary() -> None:
    pass

@ku.file(graph)
@ku.depend(built_path)
def output_graph() -> None:
    pass

@ku.file(built_path)
@ku.depend(*input_files)
def build() -> None:
    ...  # ここに出力処理を書く
    built_path.touch()  # 処理のタイムスタンプを記録する
```

こうすることで入力ファイルに更新があった場合に
適切に出力処理が実行されるようになります。

## 同人誌紹介（その2） {.column}

FIXME: 同人誌を紹介する（2~3冊）
