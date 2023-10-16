# 改行で半角スペースが入ってしまうので無駄な改行を取り除く
#
# ただし、以下は改行を取り除いてはいけないケース：
# 1. フロントマター
# 2. コードブロック内
# 3. 箇条書きの直前
# 4. ？や！で終わる場合
# 5. 空行自身

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


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Preprocess markdown file.")
    parser.add_argument("input", type=Path, help="targets to run")
    parser.add_argument("output", type=Path, help="targets to run")
    args = parser.parse_args()

    preprocess(args.input, args.output)
