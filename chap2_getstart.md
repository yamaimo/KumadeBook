---
link:
  - rel: 'stylesheet'
    href: 'countup.css'
---

# kumadeをはじめる

## インストール {#chap2_1}

ここではPythonの実行環境は用意できているものとします。
必要なら仮想環境などをセットアップしておいてください。

kumadeは`pip`コマンドで簡単にインストールできます：

```console
$ pip install kumade
```

インストールできたか確認したい場合、
次のようにバージョンを確認するといいです：

```console
$ kumade --version
0.1.0
```

## タスクの定義 {#chap2_2}

最初の`Kumadefile.py`を書いてタスクを定義してみましょう。

```python title=最初のKumadefile.py
import kumade as ku

from pathlib import Path
import subprocess

ku.set_default("greet")

help_file = Path("help.txt")

@ku.task("greet")
@ku.depend(help_file)
def greeting() -> None:
    print("Hi, this is Kumade.")
    print(f"See {help_file}.")

@ku.file(help_file)
def create_help_file() -> None:
    with help_file.open("w") as outfile:
        subprocess.run(["kumade", "-h"], stdout=outfile)
```

kumadeでは関数に`@kumade.task(name: str)`や`@kumade.file(path: Path)`といった
デコレータをつけることでタスクを定義します。
関数の内容がタスクで実行される処理です。

この例では2つのタスクを定義しています。

1つ目のタスクは`@ku.task("greet")`で定義された`"greet"`というタスクです。
このタスクは実行すると挨拶文を出力します。

このタスクには`@ku.depend(help_file)`というデコレータもついています。
これはこのタスクが`help_file`（すなわち`help.txt`というファイル）に依存することを示しています。
もし`help_file`が存在しない場合、kumadeはこのタスクを実行するよりも前に
`help_file`のファイル生成タスクを実行します。

2つ目のタスクは`@ku.file(help_file)`で定義された`help_file`のファイル生成タスクです。
このタスクは実行すると`kumade -h`の出力を`help_file`に書き出します。

この例ではその他に`ku.set_default("greet")`で
デフォルトのタスクが`"greet"`であることも指定しています。

## タスクの実行 {#chap2_3}

`Kumadefile.py`を用意してタスクが定義できたら、タスクを実行してみましょう。

実行したいタスクを引数として`kumade`コマンドを実行します：

```console
$ kumade greet
Hi, this is Kumade.
See help.txt.
```

タスクで定義した挨拶文が出力されました。

ファイルを確認すると`help.txt`も生成されています：

```console
$ ls
Kumadefile.py   help.txt   (省略)
```

中身を確認すると`kumade`コマンドのヘルプが出力されています：

```console
$ cat help.txt
usage: kumade [-h] [--version] [-f FILE] [-t] [-T] [-v] [targets ...]

A make-like build utility for Python.

positional arguments:
  targets               targets to run

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f FILE, --file FILE  use FILE as a Kumadefile
  -t, --tasks           show tasks and exit
  -T, --alltasks        show all tasks (including no description) and exit
  -v, --verbose         show task name at running
```

さて、`help.txt`のタイムスタンプを確認したあと、
少し時間をおいてからもう一度`kumade`コマンドを実行してみましょう：

```console
$ kumade
Hi, this is Kumade.
See help.txt.
```

タスクを指定せずに`kumade`コマンドを実行するとデフォルトのタスクが実行されます。

そして`help.txt`のタイムスタンプを確認してみてください。
タイムスタンプが更新されてないはずです。
すでにファイルが存在する場合、
kumadeはファイル生成タスクをスキップするのが分かるかと思います。

## 同人誌紹介（その1） {.column}

自分がこれまでに書いた同人誌を紹介します。
BOOTHなどで入手できますので、気になった方はぜひ手に取ってみてください。

### オブジェクト・ウォーズ

![](images/ObjWars.png)

https://imoarai.booth.pm/items/4773233

オブジェクト指向の入門書です。
ゲームを作りながらオブジェクト指向を学んでいきます。
オブジェクト指向でない場合との対比をすることで、
オブジェクト指向の考え方やメリットを理解しやすくしています。

### TeXグッバイしたい本

![](images/TexGoodBye.png)

https://imoarai.booth.pm/items/3604005

TeXを使わない組版を目指すシリーズです。
フォントやPDFの仕組み、組版について解説し、
独自の組版システムを構築します。
この本自体、TeXを使わずに組版しています。
