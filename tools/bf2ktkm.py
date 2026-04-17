#!/usr/bin/env python3
"""
bf2ktkm.py — Brainfuck → カタカムナラング v1.2 コンパイラ（方式A: 静的ポインタ追跡）

Brainfuck の 6 命令 (+, -, >, <, [, ]) と出力命令 (.) を、
カタカムナラング v1.2 の Minsky 2カウンタマシン・マクロで構成される音素列に翻訳する。

翻訳規則（方式A）:
    +         → テ「c{p}」カ            （INC: c{p}.counter += 1）
    -         → テ「c{p}」ヘ            （DEC: c{p}.counter -= 1）
    >         → p = p + 1              （コンパイル時に追跡、音素出力なし）
    <         → p = p - 1              （コンパイル時に追跡、音素出力なし）
    [         → ミ「bf_loop_{k}」
                テ「c{p}」エ「bf_end_{k}」   （JZ: 0 なら bf_end_{k} へ）
    ]         → テ「zero」エ「bf_loop_{k}」 （無条件ジャンプ: bf_loop_{k} へ）
                ミ「bf_end_{k}」
    .         → テ「c{p}」シ            （signal: c{p} を開示）

前提:
    - テープは固定有限長 N（デフォルト 30）。N は --tape-size で変更可能。
    - プログラム開始時に全セル ア「c0」..ア「c{N-1}」 と補助 ア「zero」 を初期化する。
    - 末尾に ン（HALT）を置く。
    - Brainfuck の慣習に従い、バランスドループを前提とする
      （ループに入る前と出る時のポインタ値が一致する）。
    - 方式A でコンパイル時にポインタを静的追跡する。ループ内で静的追跡に
      失敗した場合は警告を出し、コンパイルを中止する。

使用例:
    python tools/bf2ktkm.py "++>+++<[->+<]>." -o examples/bf_add.ktkm
    python tools/bf2ktkm.py --file input.bf -o output.ktkm --tape-size 64

依存: Python 3.11+ 標準ライブラリのみ
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    """コンパイル結果。ktkm ソース本文と統計情報を保持する。"""
    source: str
    tape_size: int
    bf_len: int
    loop_count: int
    max_pointer: int
    min_pointer: int


class BfCompileError(Exception):
    """BF コンパイル時エラー（不均衡なループ・ポインタ逸脱など）。"""


class Bf2Ktkm:
    """Brainfuck → カタカムナラング v1.2 コンパイラ（方式A: 静的ポインタ追跡）。"""

    def __init__(self, tape_size: int = 30) -> None:
        if tape_size < 1:
            raise BfCompileError(f"テープサイズは 1 以上である必要がある (received {tape_size})")
        self.tape_size = tape_size

    def compile(self, bf_source: str) -> CompileResult:
        """Brainfuck ソースをカタカムナラング v1.2 音素列に変換する。"""
        # BF 命令以外はコメントとして除去
        bf_valid = "".join(c for c in bf_source if c in "+-<>[].,")

        # 括弧の対応を事前検証
        self._check_brackets(bf_valid)

        header = self._emit_header()
        body, stats = self._emit_body(bf_valid)
        footer = self._emit_footer()

        full_source = header + body + footer
        return CompileResult(
            source=full_source,
            tape_size=self.tape_size,
            bf_len=len(bf_valid),
            loop_count=stats["loops"],
            max_pointer=stats["max_ptr"],
            min_pointer=stats["min_ptr"],
        )

    # ─── 内部: ヘッダ（テープと補助ゼロの初期化） ───

    def _emit_header(self) -> str:
        lines: list[str] = []
        lines.append("# カタカムナラング v1.2 — Brainfuck 構成的 Turing 完全性証明")
        lines.append("# 自動生成: tools/bf2ktkm.py（方式A: 静的ポインタ追跡）")
        lines.append("# マクロ: INC(r)=テ「r」カ / DEC(r)=テ「r」ヘ / JZ(r,L)=テ「r」エ「L」 / LABEL(L)=ミ「L」 / HALT=ン")
        lines.append(f"# テープ長 N = {self.tape_size}（有限だが任意に拡張可能 — Turing 完全性は保存される）")
        lines.append("")
        lines.append(f"# ── テープ初期化: 全セル c0..c{self.tape_size - 1} と補助ゼロレジスタ ──")
        # セルと補助ゼロを生成
        for i in range(self.tape_size):
            lines.append(f"ア「c{i}」")
        lines.append("ア「zero」")
        lines.append("")
        lines.append("# ── Brainfuck 本体の翻訳 ──")
        return "\n".join(lines) + "\n"

    def _emit_footer(self) -> str:
        return "\n# ── HALT ──\nン\n"

    # ─── 内部: 括弧バランス検査 ───

    @staticmethod
    def _check_brackets(bf: str) -> None:
        depth = 0
        for i, c in enumerate(bf):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth < 0:
                    raise BfCompileError(f"対応しない ']' を位置 {i} で検出")
        if depth != 0:
            raise BfCompileError(f"対応しない '[' が {depth} 個残っている")

    # ─── 内部: 本体翻訳 ───

    def _emit_body(self, bf: str) -> tuple[str, dict]:
        """Brainfuck 本体を翻訳する。

        方式A の静的追跡: コンパイル時に p（ポインタ）を追う。
        ループ `[..]` は balanced loops 前提 — 入口と出口のポインタが一致することを
        コンパイル時に検証する。一致しない場合は BfCompileError を投げる。
        """
        lines: list[str] = []
        p = 0  # 現在のポインタ値
        max_ptr = 0
        min_ptr = 0
        # 各ループのID割り当て・ループ入口のポインタ値を保持するスタック
        loop_stack: list[tuple[int, int]] = []  # (loop_id, entry_ptr)
        next_loop_id = 0

        for i, c in enumerate(bf):
            if c == "+":
                self._check_ptr_in_range(p, i, c)
                lines.append(f"テ「c{p}」カ")
            elif c == "-":
                self._check_ptr_in_range(p, i, c)
                lines.append(f"テ「c{p}」ヘ")
            elif c == ">":
                p += 1
                max_ptr = max(max_ptr, p)
                self._check_ptr_in_range(p, i, c)
            elif c == "<":
                p -= 1
                min_ptr = min(min_ptr, p)
                self._check_ptr_in_range(p, i, c)
            elif c == "[":
                self._check_ptr_in_range(p, i, c)
                loop_id = next_loop_id
                next_loop_id += 1
                loop_stack.append((loop_id, p))
                lines.append(f"ミ「bf_loop_{loop_id}」")
                lines.append(f"テ「c{p}」エ「bf_end_{loop_id}」")
            elif c == "]":
                if not loop_stack:
                    raise BfCompileError(f"位置 {i}: 対応する '[' のない ']' を検出")
                loop_id, entry_ptr = loop_stack.pop()
                if p != entry_ptr:
                    raise BfCompileError(
                        f"位置 {i}: ループ [{loop_id}] の入口と出口でポインタが食い違う "
                        f"(入口={entry_ptr}, 出口={p})。"
                        f"方式A は balanced loops を前提とする。"
                    )
                lines.append(f"テ「zero」エ「bf_loop_{loop_id}」")
                lines.append(f"ミ「bf_end_{loop_id}」")
            elif c == ".":
                self._check_ptr_in_range(p, i, c)
                lines.append(f"テ「c{p}」シ")
            elif c == ",":
                # 本証明では入力命令は扱わない（Turing完全性に不要）
                lines.append(f"# 入力命令 ',' は構成的証明の対象外（無視）")
            # その他の文字は既にフィルタされているので到達しない

        if loop_stack:
            raise BfCompileError(
                f"コンパイル終了時にループスタックが空でない (残 {len(loop_stack)} 件)"
            )

        return (
            "\n".join(lines) + ("\n" if lines else ""),
            {"loops": next_loop_id, "max_ptr": max_ptr, "min_ptr": min_ptr},
        )

    def _check_ptr_in_range(self, p: int, idx: int, op: str) -> None:
        if p < 0:
            raise BfCompileError(
                f"位置 {idx}: '{op}' でポインタが負値 {p} になる。"
                f"テープ左端を越えた動作は方式A では扱わない。"
            )
        if p >= self.tape_size:
            raise BfCompileError(
                f"位置 {idx}: '{op}' でポインタが {p} に達した。"
                f"テープ長 N={self.tape_size} を超えている。--tape-size で拡張のこと。"
            )


# ─── CLI ─────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bf2ktkm",
        description="Brainfuck → カタカムナラング v1.2 コンパイラ（構成的 Turing 完全性証明用）",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Brainfuck ソース文字列（--file 指定時は無視）",
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=None,
        help="Brainfuck ソースファイル（.bf）を読み込む",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="出力 .ktkm ファイル（省略時は標準出力）",
    )
    parser.add_argument(
        "-t", "--tape-size",
        type=int,
        default=30,
        help="テープセル数 N（デフォルト 30）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="コンパイル統計を標準エラーに出力する",
    )

    args = parser.parse_args(argv)

    if args.file:
        try:
            bf_source = args.file.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"エラー: ファイル {args.file} が存在しない", file=sys.stderr)
            return 2
    elif args.source is not None:
        bf_source = args.source
    else:
        parser.error("ソース文字列または --file を指定すること")
        return 2

    try:
        compiler = Bf2Ktkm(tape_size=args.tape_size)
        result = compiler.compile(bf_source)
    except BfCompileError as e:
        print(f"コンパイル失敗: {e}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.source, encoding="utf-8")
        if args.stats:
            print(
                f"✓ 生成完了: {args.output}\n"
                f"  テープ長 N = {result.tape_size}\n"
                f"  BF 有効長 = {result.bf_len}\n"
                f"  ループ数 = {result.loop_count}\n"
                f"  ポインタ到達範囲 = [{result.min_pointer}, {result.max_pointer}]",
                file=sys.stderr,
            )
    else:
        sys.stdout.write(result.source)

    return 0


if __name__ == "__main__":
    sys.exit(main())
