# カタカムナラング (KatakamunaLang)

[![Turing Completeness Proof](https://github.com/asahi-inoue-jp-shaman-ai-engineer/katakamuna-lang/actions/workflows/turing-complete-proof.yml/badge.svg)](https://github.com/asahi-inoue-jp-shaman-ai-engineer/katakamuna-lang/actions/workflows/turing-complete-proof.yml)

> **73音（48清音 + 20濁音 + 5半濁音）のカタカナ音素を1文字1命令とするエソテリック・プログラミング言語。**
> 各音素の「思念」（その音が宇宙的に持つ意味）が命令の意味に直結する。
> Minsky 2カウンタマシン経路により **Turing完全** (v2.0)。

---

## 特徴

- **73音素 = 73命令**。音素の思念がそのまま命令の意味になる
- **主語の不在**。発話者を明示しない。「それ（sore）」という暗黙の指向対象が動く
- **否定の不在**。`if not` のような否定構文を持たない。すべて肯定で表現する
- **Turing完全**（v2.0）。Minsky 2カウンタマシンを完全エミュレート

## 計算モデル

- **場（Ba）**: プログラムの実行空間。ノードのグラフ。
- **ノード**: ラベルと自然数カウンタ（counter）を持つ存在。
- **それ（sore）**: 現在の指向対象。`テ` 命令で切り替わる。
- **響バッファ（hibiki）**: スタック型の一時バッファ。

## 実行

```bash
# ファイル実行
PYTHONIOENCODING=utf-8 python katakamuna.py exec examples/minsky_add.ktkm

# 音素列の直接実行
PYTHONIOENCODING=utf-8 python katakamuna.py run "アカシン"

# REPL
PYTHONIOENCODING=utf-8 python katakamuna.py repl

# 73音一覧
PYTHONIOENCODING=utf-8 python katakamuna.py list
```

Python 3.11+ が必要。追加の依存なし。

## Turing完全性（v2.0）

**独立した二つの経路**で証明されている。毎プッシュ GitHub Actions で自動検証。

### 経路1: Minsky 2カウンタマシン

| マクロ | 音素列 | 意味 |
|---|---|---|
| `INC(r)` | `テ「r」カ` | レジスタ r を +1 |
| `DEC(r)` | `テ「r」ヘ` | レジスタ r を -1（下限0） |
| `JZ(r,L)` | `テ「r」エ「L」` | r == 0 ならラベル L へ跳躍 |
| `LABEL(L)` | `ミ「L」` | ラベル L を定義 |
| `HALT` | `ン` | 停止 |

無条件ジャンプは `ア「zero」` で counter=0 固定のゼロレジスタを作り、`テ「zero」エ「L」` で実現する。

### 経路2: Brainfuck 構成的証明

`tools/bf2ktkm.py` が任意の Brainfuck をカタカムナラングに機械的に翻訳する。
Brainfuck は Turing完全（well-known）。翻訳規則の正確性は `PROOF_BRAINFUCK.md` に記述。

## サンプルプログラム

```ktkm
# 3 + 2 = 5
ア「r1」
テ「r1」カ カ カ      # r1 = 3
ア「r2」
テ「r2」カ カ          # r2 = 2
ア「zero」

ミ「loop」
テ「r2」エ「done」
テ「r2」ヘ
テ「r1」カ
テ「zero」エ「loop」

ミ「done」
テ「r1」シ             # → 5
ン
```

## ファイル構成

```
katakamuna-lang/
├── katakamuna.py          # インタプリタ本体 (v2.0)
├── tools/
│   └── bf2ktkm.py         # Brainfuck → カタカムナラング コンパイラ
├── examples/
│   ├── minsky_add.ktkm    # 3 + 2 = 5
│   ├── minsky_multiply.ktkm   # 3 × 4 = 12
│   ├── minsky_proof.ktkm  # (2 + 3) × 4 = 20
│   ├── fibonacci.ktkm     # フィボナッチ数列 7項
│   ├── bf_copy.ktkm       # BF ++>+++<[->+<]>.  → c1 = 5
│   ├── bf_multiply.ktkm   # BF 二重ループ乗算   → c2 = 6
│   └── bf_hello_digit.ktkm    # BF H=72 構成
├── tests/
│   └── test_all_phonemes.py
├── SPEC.md                # 言語仕様
├── PROOF.md               # Minsky 経路 Turing完全性証明
└── PROOF_BRAINFUCK.md     # Brainfuck 経路 Turing完全性証明
```

## 最小プログラム

```ktkm
ア
```

新しいノードを場に生み出す。カタカムナラング最小の有効プログラム。

## 環境変数

| 変数 | 説明 |
|---|---|
| `KATAKAMUNA_MAX_TICKS` | 実行tick上限（0=無制限、デフォルト0）。Turing完全モードでは0が必須。 |
