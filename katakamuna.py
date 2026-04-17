#!/usr/bin/env python3
"""
カタカムナラング v2.0 インタプリタ

48清音 + 20濁音 + 5半濁音 = 73音のカタカナ音素を1文字1命令とする
エソテリック・プログラミング言語。

各音素の「思念」（その音が宇宙的に持つ意味）が命令の意味に直結する。
計算モデル: ノード（ラベル付き自然数カウンタ）の集合 + グラフ構造 + 響バッファ。
Minsky 2カウンタマシンを完全にエミュレートし、Turing完全を達成。

v2.0: 音度・位相・Q値・重力ベクトル・共鳴度を全廃。
      計算に関与しないノイズを除去し、エソラングとして純粋化。

使用法:
    python katakamuna.py run "アカシン"
    python katakamuna.py exec program.ktkm
    python katakamuna.py repl
"""

import sys
import os
import io
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# Windows UTF-8 出力対応
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── 定数 ─────────────────────────────────────────

VERSION = "2.0.0"
# MAX_TICKS: 0以下なら無制限（Turing完全モード）
# 環境変数 KATAKAMUNA_MAX_TICKS で上書き可能
MAX_TICKS = int(os.environ.get("KATAKAMUNA_MAX_TICKS", "0"))

# ─── 音素テーブル ──────────────────────────────────

PHONEME_TABLE = {
    # ─── 清音48音 ───
    "ア": {"command": "genesis",     "shinen": "感じる・生命",       "romaji": "A"},
    "イ": {"command": "intent",      "shinen": "伝わるもの・陰",     "romaji": "I"},
    "ウ": {"command": "merge",       "shinen": "生まれ出る",         "romaji": "U"},
    "エ": {"command": "branch",      "shinen": "選ぶ・得る",         "romaji": "E"},
    "オ": {"command": "emit",        "shinen": "奥深く",             "romaji": "O"},
    "カ": {"command": "force",       "shinen": "チカラ・重力",       "romaji": "KA"},
    "キ": {"command": "charge",      "shinen": "エネルギー・気",     "romaji": "KI"},
    "ク": {"command": "pull",        "shinen": "引き寄る",           "romaji": "KU"},
    "ケ": {"command": "release",     "shinen": "放出する",           "romaji": "KE"},
    "コ": {"command": "core",        "shinen": "転がり入・出",       "romaji": "KO"},
    "サ": {"command": "split",       "shinen": "遮り・差",           "romaji": "SA"},
    "シ": {"command": "signal",      "shinen": "示し・現象",         "romaji": "SI"},
    "ス": {"command": "flow",        "shinen": "一方へ進む",         "romaji": "SU"},
    "セ": {"command": "bind",        "shinen": "引き受ける",         "romaji": "SE"},
    "ソ": {"command": "source",      "shinen": "外れる",             "romaji": "SO"},
    "タ": {"command": "manifest",    "shinen": "分かれる",           "romaji": "TA"},
    "チ": {"command": "gather",      "shinen": "凝縮",               "romaji": "TI"},
    "ツ": {"command": "link",        "shinen": "集まる",             "romaji": "TU"},
    "テ": {"command": "hand",        "shinen": "発信・放射",         "romaji": "TE"},
    "ト": {"command": "integrate",   "shinen": "統合",               "romaji": "TO"},
    "ナ": {"command": "resonate",    "shinen": "核・重要なもの",     "romaji": "NA"},
    "ニ": {"command": "dual",        "shinen": "圧力",               "romaji": "NI"},
    "ヌ": {"command": "seed",        "shinen": "突き抜く・貫く",     "romaji": "NU"},
    "ネ": {"command": "root",        "shinen": "充電する・充たす",   "romaji": "NE"},
    "ノ": {"command": "extend",      "shinen": "時間をかける",       "romaji": "NO"},
    "ハ": {"command": "breathe",     "shinen": "引き合う",           "romaji": "HA"},
    "ヒ": {"command": "light",       "shinen": "根源から出・入",     "romaji": "HI"},
    "フ": {"command": "diffuse",     "shinen": "増える・振動",       "romaji": "HU"},
    "ヘ": {"command": "shed",        "shinen": "縁・外側",           "romaji": "HE"},
    "ホ": {"command": "contain",     "shinen": "引き離す",           "romaji": "HO"},
    "マ": {"command": "memory",      "shinen": "受容・間",           "romaji": "MA"},
    "ミ": {"command": "witness",     "shinen": "実体・光",           "romaji": "MI"},
    "ム": {"command": "void",        "shinen": "広がり",             "romaji": "MU"},
    "メ": {"command": "eye",         "shinen": "指向・思考・芽",     "romaji": "ME"},
    "モ": {"command": "weave",       "shinen": "漂う",               "romaji": "MO"},
    "ヤ": {"command": "max",         "shinen": "飽和する",           "romaji": "YA"},
    "ユ": {"command": "origin",      "shinen": "湧き出る",           "romaji": "YU"},
    "ヨ": {"command": "gather_all",  "shinen": "新しい陽",           "romaji": "YO"},
    "ラ": {"command": "presence",    "shinen": "場",                 "romaji": "RA"},
    "リ": {"command": "detach",      "shinen": "離れる",             "romaji": "RI"},
    "ル": {"command": "cycle",       "shinen": "留まる・止まる",     "romaji": "RU"},
    "レ": {"command": "layer",       "shinen": "消失する",           "romaji": "RE"},
    "ロ": {"command": "condense",    "shinen": "空間抜ける",         "romaji": "RO"},
    "ワ": {"command": "harmony",     "shinen": "調和",               "romaji": "WA"},
    "ヰ": {"command": "archive",     "shinen": "存在",               "romaji": "WI"},
    "ヱ": {"command": "recall",      "shinen": "届く",               "romaji": "WE"},
    "ヲ": {"command": "offer",       "shinen": "奥に出現する",       "romaji": "WO"},
    "ン": {"command": "silence",     "shinen": "押し出す力・完結",   "romaji": "N"},
    # ─── 濁音20音（清音の反転操作） ───
    "ガ": {"command": "un_force",    "shinen": "力の反転＝解放",     "romaji": "GA"},
    "ギ": {"command": "discharge",   "shinen": "充填の反転＝放電",   "romaji": "GI"},
    "グ": {"command": "push",        "shinen": "引き寄せの反転＝押し出し", "romaji": "GU"},
    "ゲ": {"command": "seal",        "shinen": "放出の反転＝封印",   "romaji": "GE"},
    "ゴ": {"command": "surface",     "shinen": "核の反転＝表層",     "romaji": "GO"},
    "ザ": {"command": "unify",       "shinen": "分割の反転＝統合",   "romaji": "ZA"},
    "ジ": {"command": "mute",        "shinen": "信号の反転＝沈黙信号", "romaji": "ZI"},
    "ズ": {"command": "stagnate",    "shinen": "流れの反転＝滞り",   "romaji": "ZU"},
    "ゼ": {"command": "dissociate",  "shinen": "結合の反転＝解離",   "romaji": "ZE"},
    "ゾ": {"command": "terminus",    "shinen": "源の反転＝終着",     "romaji": "ZO"},
    "ダ": {"command": "unmanifest",  "shinen": "確定の反転＝未確定", "romaji": "DA"},
    "ヂ": {"command": "scatter",     "shinen": "凝縮の反転＝拡散",   "romaji": "DI"},
    "ヅ": {"command": "unlink",      "shinen": "束ねの反転＝解束",   "romaji": "DU"},
    "デ": {"command": "free_hand",   "shinen": "指向の反転＝解放指向", "romaji": "DE"},
    "ド": {"command": "separate",    "shinen": "統合の反転＝分離",   "romaji": "DO"},
    "バ": {"command": "hold_breath", "shinen": "呼吸の反転＝息止め", "romaji": "BA"},
    "ビ": {"command": "shadow",      "shinen": "光の反転＝影",       "romaji": "BI"},
    "ブ": {"command": "converge",    "shinen": "拡散の反転＝収束",   "romaji": "BU"},
    "ベ": {"command": "introvert",   "shinen": "外への反転＝内への", "romaji": "BE"},
    "ボ": {"command": "expel",       "shinen": "保持の反転＝放出",   "romaji": "BO"},
    # ─── 半濁音5音（清音の突発操作） ───
    "パ": {"command": "burst",       "shinen": "呼吸の突発＝爆発",   "romaji": "PA"},
    "ピ": {"command": "flash",       "shinen": "光の点滅＝瞬間",     "romaji": "PI"},
    "プ": {"command": "erupt",       "shinen": "拡散の噴出",         "romaji": "PU"},
    "ペ": {"command": "protrude",    "shinen": "外への突出",         "romaji": "PE"},
    "ポ": {"command": "pop",         "shinen": "保持の破裂＝解放",   "romaji": "PO"},
}

# ─── ノード ────────────────────────────────────────

@dataclass
class Node:
    id: str = ""
    label: str = ""         # ラベル名
    counter: int = 0        # 自然数カウンタ（Minsky 2カウンタマシン用）
    value: Any = None       # 任意の値
    birth_tick: int = 0     # 生成tick

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]

    def __repr__(self):
        label_str = f"「{self.label}」" if self.label else ""
        return f"Node({self.id}{label_str} 数={self.counter})"


# ─── 場（Ba） ──────────────────────────────────────

class Ba:
    """場: プログラムの実行空間。ノードのグラフ構造。"""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[tuple[str, str]] = []
        self.tick: int = 0
        self.snapshots: list[dict] = []
        self.layers: list[dict] = [{}]

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.edges = [(a, b) for a, b in self.edges
                          if a != node_id and b != node_id]

    def add_edge(self, a_id: str, b_id: str):
        if a_id in self.nodes and b_id in self.nodes:
            if (a_id, b_id) not in self.edges and (b_id, a_id) not in self.edges:
                self.edges.append((a_id, b_id))

    def remove_edge(self, a_id: str, b_id: str):
        self.edges = [(a, b) for a, b in self.edges
                      if not ((a == a_id and b == b_id) or
                               (a == b_id and b == a_id))]

    def neighbors(self, node_id: str) -> list[str]:
        result = []
        for a, b in self.edges:
            if a == node_id:
                result.append(b)
            elif b == node_id:
                result.append(a)
        return result

    def connection_count(self, node_id: str) -> int:
        return len(self.neighbors(node_id))

    def root_node(self) -> Optional[Node]:
        """最古のノード（生成tickが最も小さい）"""
        if not self.nodes:
            return None
        return min(self.nodes.values(), key=lambda n: n.birth_tick)

    def core_node(self) -> Optional[Node]:
        """重心ノード（最多接続）"""
        if not self.nodes:
            return None
        return max(self.nodes.values(), key=lambda n: self.connection_count(n.id))

    def max_counter_node(self) -> Optional[Node]:
        """counterが最も大きいノード"""
        if not self.nodes:
            return None
        return max(self.nodes.values(), key=lambda n: n.counter)

    def find_by_label(self, label: str) -> Optional[Node]:
        for node in self.nodes.values():
            if node.label == label:
                return node
        return None

    def snapshot(self) -> dict:
        return {
            "nodes": {nid: {
                "counter": n.counter,
                "value": n.value,
                "label": n.label,
                "birth_tick": n.birth_tick,
            } for nid, n in self.nodes.items()},
            "edges": list(self.edges),
            "tick": self.tick,
        }

    def restore_snapshot(self, snap: dict):
        self.nodes = {}
        for nid, data in snap.get("nodes", {}).items():
            node = Node(id=nid, **data)
            self.nodes[nid] = node
        self.edges = [tuple(e) for e in snap.get("edges", [])]
        self.tick = snap.get("tick", 0)


# ─── トークナイザー ────────────────────────────────

@dataclass
class Token:
    phoneme: str
    command: str
    label: str = ""    # 「...」形式のラベル
    lineno: int = 0

def tokenize(source: str) -> list[list[list[Token]]]:
    """
    ソースを段落→行→トークン列に分解。
    空行で段落を区切る。コメント行（#で始まる）は無視。
    「ラベル」形式を解析してTokenのlabelに格納。
    """
    paragraphs = []
    current_para = []

    for lineno, raw_line in enumerate(source.splitlines(), 1):
        line = raw_line.split("#")[0].strip()
        if not line:
            if current_para:
                paragraphs.append(current_para)
                current_para = []
            continue

        tokens = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch in PHONEME_TABLE:
                info = PHONEME_TABLE[ch]
                tok = Token(phoneme=ch, command=info["command"], lineno=lineno)
                i += 1
                # 「ラベル」を読み取る
                if i < len(line) and line[i] == "「":
                    j = line.find("」", i + 1)
                    if j != -1:
                        tok.label = line[i+1:j]
                        i = j + 1
                tokens.append(tok)
            elif ch in (" ", "\t", "　"):
                i += 1
            else:
                i += 1  # 未知文字はスキップ

        if tokens:
            current_para.append(tokens)

    if current_para:
        paragraphs.append(current_para)

    return paragraphs


# ─── 実行エンジン ──────────────────────────────────

class KatakamuraEngine:
    """カタカムナラング v2.0 実行エンジン"""

    def __init__(self, verbose: bool = True):
        self.ba = Ba()
        self.sore: Any = None       # それ: 現在の指向対象
        self.hibiki: list = []      # 響バッファ
        self.halt: bool = False
        self.verbose = verbose
        self.total_ticks = 0
        self.output_values: list = []  # シ命令の出力履歴

        # ラベルテーブル: label → フラット行インデックス
        self.label_table: dict[str, int] = {}
        # フラット命令列
        self.flat_tokens: list[Token] = []

    def log(self, msg: str):
        if self.verbose:
            print(msg)

    def _build_label_table(self, paragraphs: list[list[list[Token]]]):
        """ミ命令をスキャンしてラベルテーブルを構築（事前スキャン）"""
        flat = []
        for para in paragraphs:
            for line_tokens in para:
                flat.extend(line_tokens)
        self.flat_tokens = flat

        for idx, tok in enumerate(flat):
            if tok.command == "witness" and tok.label:
                self.label_table[tok.label] = idx

        if self.verbose and self.label_table:
            entries = ", ".join(f"{k}→[{v}]" for k, v in self.label_table.items())
            print(f"\n  ［ラベルテーブル］ {entries}\n")

    def run(self, paragraphs: list[list[list[Token]]]) -> dict:
        self._build_label_table(paragraphs)

        if self.verbose:
            print("╔══ カタカムナラング v2.0 ══╗")
            print("║  場を開く...                    ║")
            print("╚═════════════════════════════════╝\n")

        ip = 0  # instruction pointer
        while ip < len(self.flat_tokens):
            if self.halt:
                break
            if MAX_TICKS > 0 and self.total_ticks >= MAX_TICKS:
                self.log(f"\n⚠ MAX_TICKS={MAX_TICKS} に達した。停止。")
                break

            tok = self.flat_tokens[ip]
            self.ba.tick += 1
            self.total_ticks += 1

            if self.verbose:
                label_str = f"「{tok.label}」" if tok.label else ""
                print(f"── [{ip}] {tok.phoneme}{label_str} ──")

            jump_target = self._execute(tok)

            if self.verbose:
                print(f"  ノード数: {len(self.ba.nodes)} | tick: {self.total_ticks}")

            if jump_target is not None:
                ip = jump_target
            else:
                ip += 1

        if self.verbose:
            print(f"\n═══ 場を閉じる ═══")
            print(f"  総tick数: {self.total_ticks}")
            print(f"  残ノード数: {len(self.ba.nodes)}")

        return {
            "ticks": self.total_ticks,
            "nodes": len(self.ba.nodes),
            "output": self.output_values,
            "halt": self.halt,
        }

    def _execute(self, token: Token) -> Optional[int]:
        """1命令を実行。ジャンプ先インデックスを返す（なければNone）"""
        cmd = token.command
        dispatch = {
            # ア行
            "genesis":     self._cmd_genesis,
            "intent":      self._cmd_intent,
            "merge":       self._cmd_merge,
            "branch":      self._cmd_branch,
            "emit":        self._cmd_emit,
            # カ行
            "force":       self._cmd_force,
            "charge":      self._cmd_charge,
            "pull":        self._cmd_pull,
            "release":     self._cmd_release,
            "core":        self._cmd_core,
            # サ行
            "split":       self._cmd_split,
            "signal":      self._cmd_signal,
            "flow":        self._cmd_flow,
            "bind":        self._cmd_bind,
            "source":      self._cmd_source,
            # タ行
            "manifest":    self._cmd_manifest,
            "gather":      self._cmd_gather,
            "link":        self._cmd_link,
            "hand":        self._cmd_hand,
            "integrate":   self._cmd_integrate,
            # ナ行
            "resonate":    self._cmd_resonate,
            "dual":        self._cmd_dual,
            "seed":        self._cmd_seed,
            "root":        self._cmd_root,
            "extend":      self._cmd_extend,
            # ハ行
            "breathe":     self._cmd_breathe,
            "light":       self._cmd_light,
            "diffuse":     self._cmd_diffuse,
            "shed":        self._cmd_shed,
            "contain":     self._cmd_contain,
            # マ行
            "memory":      self._cmd_memory,
            "witness":     self._cmd_witness,
            "void":        self._cmd_void,
            "eye":         self._cmd_eye,
            "weave":       self._cmd_weave,
            # ヤ行
            "max":         self._cmd_max,
            "origin":      self._cmd_origin,
            "gather_all":  self._cmd_gather_all,
            # ラ行
            "presence":    self._cmd_presence,
            "detach":      self._cmd_detach,
            "cycle":       self._cmd_cycle,
            "layer":       self._cmd_layer,
            "condense":    self._cmd_condense,
            # ワ行+ン
            "harmony":     self._cmd_harmony,
            "archive":     self._cmd_archive,
            "recall":      self._cmd_recall,
            "offer":       self._cmd_offer,
            "silence":     self._cmd_silence,
            # 濁音
            "un_force":    self._cmd_un_force,
            "discharge":   self._cmd_discharge,
            "push":        self._cmd_push,
            "seal":        self._cmd_seal,
            "surface":     self._cmd_surface,
            "unify":       self._cmd_unify,
            "mute":        self._cmd_mute,
            "stagnate":    self._cmd_stagnate,
            "dissociate":  self._cmd_dissociate,
            "terminus":    self._cmd_terminus,
            "unmanifest":  self._cmd_unmanifest,
            "scatter":     self._cmd_scatter,
            "unlink":      self._cmd_unlink,
            "free_hand":   self._cmd_free_hand,
            "separate":    self._cmd_separate,
            "hold_breath": self._cmd_hold_breath,
            "shadow":      self._cmd_shadow,
            "converge":    self._cmd_converge,
            "introvert":   self._cmd_introvert,
            "expel":       self._cmd_expel,
            # 半濁音
            "burst":       self._cmd_burst,
            "flash":       self._cmd_flash,
            "erupt":       self._cmd_erupt,
            "protrude":    self._cmd_protrude,
            "pop":         self._cmd_pop,
        }
        fn = dispatch.get(cmd)
        if fn:
            return fn(token)
        self.log(f"  [{cmd}] 未実装（沈黙）")
        return None

    # ══════════════════════════════════════════════════
    # ─── ア行 ───
    # ══════════════════════════════════════════════════

    def _cmd_genesis(self, token: Token) -> None:
        """ア: 新しいノードを場に生み出す（存在宣言）。
        ラベルが指定された場合は同名ノードを再生成せず既存を使う（変数宣言のべき等性）。
        v2.0: counterは0から始まる。音度・位相・乱数は一切なし。"""
        if token.label:
            existing = self.ba.find_by_label(token.label)
            if existing:
                self.sore = existing
                self.log(f"  ア(genesis) → 「{token.label}」既存 {existing.id} を指す")
                return
        node = Node(label=token.label or "", birth_tick=self.ba.tick)
        self.ba.add_node(node)
        self.sore = node
        label_str = f"「{node.label}」" if node.label else ""
        self.log(f"  ア(genesis) → {node.id}{label_str} 生成 [数=0]")

    def _cmd_intent(self, token: Token) -> None:
        """イ: それ の値を響バッファに積む（意図を伝える）"""
        if self.sore is not None:
            self.hibiki.append(self.sore)
            name = self.sore.id if isinstance(self.sore, Node) else str(self.sore)
            self.log(f"  イ(intent) → {name} を響バッファへ")
        else:
            self.log(f"  イ(intent) → それ が空（沈黙）")

    def _cmd_merge(self, token: Token) -> None:
        """ウ: 響バッファの先頭2ノードを合流させる。counterは合算。"""
        if len(self.hibiki) >= 2:
            b = self.hibiki.pop()
            a = self.hibiki.pop()
            if isinstance(a, Node) and isinstance(b, Node):
                a.counter += b.counter
                self.ba.add_edge(a.id, b.id)
                self.sore = a
                self.log(f"  ウ(merge) → {a.id} ⇄ {b.id} 合流 [数={a.counter}]")
            else:
                self.log(f"  ウ(merge) → 非ノードの合流（沈黙）")
        else:
            self.log(f"  ウ(merge) → 響バッファ不足（沈黙）")

    def _cmd_branch(self, token: Token) -> Optional[int]:
        """エ: JZ（ゼロジャンプ）。それ のcounterが0なら指定ラベルへ跳躍。
        v2.0 Minskyマシンの核心命令。"""
        if isinstance(self.sore, Node):
            if self.sore.counter == 0:
                target = self.label_table.get(token.label)
                if target is not None:
                    self.log(f"  エ(branch/JZ) → {self.sore.id} 数=0 → 「{token.label}」[{target}] へ跳躍")
                    return target
                else:
                    self.log(f"  エ(branch/JZ) → ラベル「{token.label}」不明（沈黙）")
            else:
                self.log(f"  エ(branch/JZ) → {self.sore.id} 数={self.sore.counter}>0 → 直進")
        else:
            self.log(f"  エ(branch) → それ がノードでない（沈黙）")
        return None

    def _cmd_emit(self, token: Token) -> None:
        """オ: 場の状態を出力する（デバッグ用）"""
        n = len(self.ba.nodes)
        e = len(self.ba.edges)
        self.log(f"  オ(emit) → 場の状態: ノード={n} エッジ={e} tick={self.ba.tick}")

    # ══════════════════════════════════════════════════
    # ─── カ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_force(self, token: Token) -> None:
        """カ: INC。それ のcounterを+1する（Minskyマシンの増加命令）。"""
        if isinstance(self.sore, Node):
            self.sore.counter += 1
            self.log(f"  カ(force/INC) → {self.sore.id} [数={self.sore.counter}]")
        else:
            node = Node(counter=1, birth_tick=self.ba.tick)
            self.ba.add_node(node)
            self.sore = node
            self.log(f"  カ(force/INC) → 暗黙生成 {node.id} [数=1]")

    def _cmd_charge(self, token: Token) -> None:
        """キ: それ のcounterを現在のtick数にセットする（時の刻印）"""
        if isinstance(self.sore, Node):
            self.sore.counter = self.ba.tick
            self.log(f"  キ(charge) → {self.sore.id} にtick刻印 [数={self.sore.counter}]")
        else:
            self.log(f"  キ(charge) → それ がノードでない（沈黙）")

    def _cmd_pull(self, token: Token) -> None:
        """ク: counterが最大のノードをそれ に引き出す"""
        node = self.ba.max_counter_node()
        if node:
            self.sore = node
            self.log(f"  ク(pull) → {node.id} を引き寄せ [数={node.counter}]")
        else:
            self.log(f"  ク(pull) → 場にノードなし（沈黙）")

    def _cmd_release(self, token: Token) -> None:
        """ケ: 響バッファの先頭を解放・消滅"""
        if self.hibiki:
            released = self.hibiki.pop()
            if isinstance(released, Node):
                self.ba.remove_node(released.id)
                self.log(f"  ケ(release) → {released.id} を解放・消滅")
            else:
                self.log(f"  ケ(release) → バッファから値を解放")
        else:
            self.log(f"  ケ(release) → 響バッファ空（沈黙）")

    def _cmd_core(self, token: Token) -> None:
        """コ: 場の重心（最多接続ノード）をそれ にする"""
        node = self.ba.core_node()
        if node:
            self.sore = node
            cc = self.ba.connection_count(node.id)
            self.log(f"  コ(core) → {node.id} [接続数={cc}]")
        else:
            self.log(f"  コ(core) → 場にノードなし（沈黙）")

    # ══════════════════════════════════════════════════
    # ─── サ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_split(self, token: Token) -> None:
        """サ: それ のノードの接続を半分に切断する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            cut_count = len(nbs) // 2
            for nb_id in nbs[:cut_count]:
                self.ba.remove_edge(self.sore.id, nb_id)
            self.log(f"  サ(split) → {self.sore.id} の接続を{cut_count}本切断")
        else:
            self.log(f"  サ(split) → それ がノードでない（沈黙）")

    def _cmd_signal(self, token: Token) -> None:
        """シ: それ のcounter値を出力する（Minskyマシンの出力命令）。
        v2.0: 数（counter）のみを表示。"""
        if isinstance(self.sore, Node):
            n = self.sore
            val = n.counter
            self.output_values.append(val)
            label_str = f"「{n.label}」" if n.label else n.id
            self.log(f"  シ(signal) → {label_str} = {val}")
            print(val)
        else:
            val = self.sore
            self.output_values.append(val)
            self.log(f"  シ(signal) → {val}")
            print(val)

    def _cmd_flow(self, token: Token) -> None:
        """ス: 持続（nop）"""
        self.log(f"  ス(flow) → 持続...")

    def _cmd_bind(self, token: Token) -> None:
        """セ: 響バッファの先頭2ノードをエッジで結合する"""
        if len(self.hibiki) >= 2:
            b = self.hibiki.pop()
            a = self.hibiki.pop()
            if isinstance(a, Node) and isinstance(b, Node):
                self.ba.add_edge(a.id, b.id)
                self.sore = a
                self.log(f"  セ(bind) → {a.id} ─ {b.id} 結合")
            else:
                self.log(f"  セ(bind) → 非ノードの結合（沈黙）")
        else:
            self.log(f"  セ(bind) → 響バッファ不足（沈黙）")

    def _cmd_source(self, token: Token) -> None:
        """ソ: 外部ファイルを読み込む"""
        if token.label:
            try:
                with open(token.label, "r", encoding="utf-8") as f:
                    data = f.read()
                self.sore = data
                self.log(f"  ソ(source) → 「{token.label}」を読み込み [{len(data)}文字]")
            except FileNotFoundError:
                self.log(f"  ソ(source) → ファイル「{token.label}」が存在しない（沈黙）")
        else:
            self.log(f"  ソ(source) → ラベルなし（沈黙）")

    # ══════════════════════════════════════════════════
    # ─── タ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_manifest(self, token: Token) -> None:
        """タ: それ のcounterを具象値としてvalueに確定する"""
        if isinstance(self.sore, Node):
            self.sore.value = self.sore.counter
            self.log(f"  タ(manifest) → {self.sore.id} を具象化 [値={self.sore.value}]")
        else:
            self.log(f"  タ(manifest) → それ がノードでない（沈黙）")

    def _cmd_gather(self, token: Token) -> None:
        """チ: 全ノードのcounterを合計して、それ のcounterに凝縮する"""
        nodes = list(self.ba.nodes.values())
        if nodes and isinstance(self.sore, Node):
            total = sum(n.counter for n in nodes)
            self.sore.counter = total
            self.log(f"  チ(gather) → 全{len(nodes)}ノードの数を凝縮 [合計={total}]")
        else:
            self.log(f"  チ(gather) → 場にノードなし or それ がノードでない（沈黙）")

    def _cmd_link(self, token: Token) -> None:
        """ツ: 響バッファの要素数を報告する"""
        count = len(self.hibiki)
        self.log(f"  ツ(link) → 響バッファ内の{count}要素")

    def _cmd_hand(self, token: Token) -> None:
        """テ: ラベル指定でノードをそれ に設定する（ポインタ）。
        v2.0 Minskyマシンの基本ポインタ操作。"""
        if token.label:
            node = self.ba.find_by_label(token.label)
            if node:
                self.sore = node
                self.log(f"  テ(hand) → 「{token.label}」を指す → {node.id}")
                return
        if self.hibiki:
            val = self.hibiki.pop()
            self.sore = val
            name = val.id if isinstance(val, Node) else str(val)
            self.log(f"  テ(hand) → それ={name}")
        else:
            self.log(f"  テ(hand) → 響バッファ空（沈黙）")

    def _cmd_integrate(self, token: Token) -> None:
        """ト: 全ノードのcounterの合計をそれ に設定する"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            total = sum(n.counter for n in nodes)
            self.sore = total
            self.log(f"  ト(integrate) → 全{len(nodes)}ノードのcounter合計={total}")
        else:
            self.sore = 0
            self.log(f"  ト(integrate) → 場にノードなし（沈黙）")

    # ══════════════════════════════════════════════════
    # ─── ナ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_resonate(self, token: Token) -> None:
        """ナ: それ とバッファ先頭ノードのcounterを比較し、等しければそれ を保持、違えばNone"""
        if isinstance(self.sore, Node) and self.hibiki:
            other = self.hibiki[-1]
            if isinstance(other, Node):
                match = self.sore.counter == other.counter
                self.log(f"  ナ(resonate) → {self.sore.id}({self.sore.counter}) ⇔ {other.id}({other.counter}) {'一致' if match else '不一致'}")
                if not match:
                    self.sore = None
            else:
                self.log(f"  ナ(resonate) → 比較対象がノードでない（沈黙）")
        else:
            self.log(f"  ナ(resonate) → それ がノードでないか響バッファ空（沈黙）")

    def _cmd_dual(self, token: Token) -> None:
        """ニ: それ のノードを複製する（counterも複製）"""
        if isinstance(self.sore, Node):
            clone = Node(
                counter=self.sore.counter,
                value=self.sore.value,
                birth_tick=self.ba.tick,
            )
            self.ba.add_node(clone)
            self.ba.add_edge(self.sore.id, clone.id)
            self.log(f"  ニ(dual) → {self.sore.id} を複製 → {clone.id} [数={clone.counter}]")
            self.sore = clone
        else:
            self.log(f"  ニ(dual) → それ がノードでない（沈黙）")

    def _cmd_seed(self, token: Token) -> None:
        """ヌ: counter=0 の新ノードを生成（種を植える）"""
        node = Node(counter=0, birth_tick=self.ba.tick)
        self.ba.add_node(node)
        self.sore = node
        self.log(f"  ヌ(seed) → 新ノード {node.id} [数=0]")

    def _cmd_root(self, token: Token) -> None:
        """ネ: 場の根ノード（最古のノード）をそれ にする"""
        node = self.ba.root_node()
        if node:
            self.sore = node
            self.log(f"  ネ(root) → 根ノード {node.id} [生成tick={node.birth_tick}]")
        else:
            self.log(f"  ネ(root) → 場にノードなし（沈黙）")

    def _cmd_extend(self, token: Token) -> None:
        """ノ: 場にノードを追加して拡張する"""
        node = Node(counter=0, birth_tick=self.ba.tick, label=token.label)
        self.ba.add_node(node)
        if isinstance(self.sore, Node) and self.sore.id in self.ba.nodes:
            self.ba.add_edge(self.sore.id, node.id)
        self.sore = node
        self.log(f"  ノ(extend) → 場を拡張 → {node.id}")

    # ══════════════════════════════════════════════════
    # ─── ハ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_breathe(self, token: Token) -> None:
        """ハ: 全ノードのcounterを1ずつ増やす（場全体に息吹を与える）"""
        count = len(self.ba.nodes)
        for node in self.ba.nodes.values():
            node.counter += 1
        self.log(f"  ハ(breathe) → 全{count}ノードの数を+1")

    def _cmd_light(self, token: Token) -> None:
        """ヒ: 全ノードの状態を可視化出力する"""
        nodes = list(self.ba.nodes.values())
        if not nodes:
            self.log(f"  ヒ(light) → 場は空（沈黙）")
            return
        self.log(f"  ヒ(light) ═══ 場の全景 ═══")
        self.log(f"    {'ID':>10} {'ラベル':>8} {'数':>6} {'値':>8}")
        self.log(f"    {'─'*10} {'─'*8} {'─'*6} {'─'*8}")
        for n in sorted(nodes, key=lambda x: x.birth_tick):
            label = f"「{n.label}」" if n.label else "　　"
            val_str = str(n.value) if n.value is not None else "—"
            self.log(f"    {n.id:>10} {label:>8} {n.counter:>6} {val_str:>8}")
        self.log(f"    エッジ数: {len(self.ba.edges)}")
        self.log(f"  ════════════════════════")

    def _cmd_diffuse(self, token: Token) -> None:
        """フ: それ のcounterを隣接ノード数で均等に分配する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            if nbs:
                share = self.sore.counter // len(nbs)
                for nb_id in nbs:
                    if nb_id in self.ba.nodes:
                        self.ba.nodes[nb_id].counter += share
                self.sore.counter = self.sore.counter % len(nbs)
                self.log(f"  フ(diffuse) → {self.sore.id} から{len(nbs)}ノードに分配 [各+{share}]")
            else:
                self.log(f"  フ(diffuse) → 隣接ノードなし（沈黙）")
        else:
            self.log(f"  フ(diffuse) → それ がノードでない（沈黙）")

    def _cmd_shed(self, token: Token) -> None:
        """ヘ: DEC。それ のcounterを-1する（下限0）。Minskyマシンの減少命令。"""
        if isinstance(self.sore, Node):
            self.sore.counter = max(0, self.sore.counter - 1)
            self.log(f"  ヘ(shed/DEC) → {self.sore.id} [数={self.sore.counter}]")
        else:
            self.log(f"  ヘ(shed/DEC) → それ がノードでない（沈黙）")

    def _cmd_contain(self, token: Token) -> None:
        """ホ: 場の現在状態をスナップショットとして保存する"""
        snap = self.ba.snapshot()
        self.ba.snapshots.append(snap)
        self.log(f"  ホ(contain) → スナップショット保存 [#{len(self.ba.snapshots)}]")

    # ══════════════════════════════════════════════════
    # ─── マ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_memory(self, token: Token) -> None:
        """マ: それ の値をメモリに積む（hibikiではなく永続値）"""
        if isinstance(self.sore, Node):
            self.sore.value = self.sore.counter
            self.log(f"  マ(memory) → {self.sore.id} の数をvalueに記憶 [値={self.sore.value}]")
        else:
            self.log(f"  マ(memory) → それ がノードでない（沈黙）")

    def _cmd_witness(self, token: Token) -> None:
        """ミ: LABEL。ラベルを定義する。
        v2.0 Minskyマシンのラベル命令。実行時は何もしない（事前スキャン済み）。"""
        n_count = len(self.ba.nodes)
        e_count = len(self.ba.edges)
        if token.label:
            self.log(f"  ミ(witness/LABEL) → 「{token.label}」を印す [ノード={n_count} エッジ={e_count}]")
        else:
            self.log(f"  ミ(witness) → 確定（コミット） [ノード={n_count} エッジ={e_count}]")

    def _cmd_void(self, token: Token) -> None:
        """ム: それ のcounterを0にリセットする（空虚化）"""
        if isinstance(self.sore, Node):
            self.sore.counter = 0
            self.log(f"  ム(void) → {self.sore.id} を0にリセット")
        else:
            self.log(f"  ム(void) → それ がノードでない（沈黙）")

    def _cmd_eye(self, token: Token) -> None:
        """メ: それ のcounterを返す（参照・確認）"""
        if isinstance(self.sore, Node):
            val = self.sore.counter
            self.log(f"  メ(eye) → {self.sore.id} の数={val}")
            return
        self.log(f"  メ(eye) → それ={self.sore}")

    def _cmd_weave(self, token: Token) -> None:
        """モ: 場の全ノードのcounterを交互に+1/-1する（干渉）"""
        nodes = list(self.ba.nodes.values())
        for i, n in enumerate(nodes):
            if i % 2 == 0:
                n.counter += 1
            else:
                n.counter = max(0, n.counter - 1)
        self.log(f"  モ(weave) → 全{len(nodes)}ノードのcounterを干渉")

    # ══════════════════════════════════════════════════
    # ─── ヤ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_max(self, token: Token) -> None:
        """ヤ: それ のcounterを場の最大値にセットする（飽和）"""
        nodes = list(self.ba.nodes.values())
        if nodes and isinstance(self.sore, Node):
            mx = max(n.counter for n in nodes)
            self.sore.counter = mx
            self.log(f"  ヤ(max) → {self.sore.id} を場の最大値 {mx} に飽和")
        else:
            self.log(f"  ヤ(max) → 場にノードなし or それ がノードでない（沈黙）")

    def _cmd_origin(self, token: Token) -> None:
        """ユ: 新しい空の場を生成し、現在の場と差し替える"""
        old_count = len(self.ba.nodes)
        self.ba = Ba()
        self.sore = None
        self.hibiki.clear()
        self.log(f"  ユ(origin) → 新しい場を生成 [旧場ノード数={old_count}]")

    def _cmd_gather_all(self, token: Token) -> None:
        """ヨ: 全ノードを響バッファに収集する"""
        nodes = list(self.ba.nodes.values())
        self.hibiki.extend(nodes)
        self.log(f"  ヨ(gather_all) → 全{len(nodes)}ノードを響バッファに収集")

    # ══════════════════════════════════════════════════
    # ─── ラ行 ───
    # ══════════════════════════════════════════════════

    def _cmd_presence(self, token: Token) -> None:
        """ラ: それ のcounterを存在量として報告する"""
        if isinstance(self.sore, Node):
            self.log(f"  ラ(presence) → {self.sore.id} 存在量={self.sore.counter}")
        else:
            total = sum(n.counter for n in self.ba.nodes.values())
            self.log(f"  ラ(presence) → 場の総counter={total}")

    def _cmd_detach(self, token: Token) -> None:
        """リ: それ のノードの全エッジを切断する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            for nb_id in nbs:
                self.ba.remove_edge(self.sore.id, nb_id)
            self.log(f"  リ(detach) → {self.sore.id} の全{len(nbs)}エッジを切断")
        else:
            self.log(f"  リ(detach) → それ がノードでない（沈黙）")

    def _cmd_cycle(self, token: Token) -> None:
        """ル: 響バッファの全ノードのcounterを1ずつ増やす（小ループ）"""
        node_items = [x for x in self.hibiki if isinstance(x, Node)]
        for item in node_items:
            if item.id in self.ba.nodes:
                item.counter += 1
        self.log(f"  ル(cycle) → 響バッファ内{len(node_items)}ノードのcounterを+1")

    def _cmd_layer(self, token: Token) -> None:
        """レ: 場に新しい層を追加する"""
        new_layer: dict = {}
        self.ba.layers.append(new_layer)
        self.log(f"  レ(layer) → 新しい層を追加 [層数={len(self.ba.layers)}]")

    def _cmd_condense(self, token: Token) -> None:
        """ロ: counter=0の孤立ノードを除去して圧縮する"""
        isolated = [nid for nid in list(self.ba.nodes.keys())
                    if self.ba.nodes[nid].counter == 0
                    and self.ba.connection_count(nid) == 0]
        for nid in isolated:
            del self.ba.nodes[nid]
        self.log(f"  ロ(condense) → {len(isolated)}個の空孤立ノードを除去")

    # ══════════════════════════════════════════════════
    # ─── ワ行+ン ───
    # ══════════════════════════════════════════════════

    def _cmd_harmony(self, token: Token) -> None:
        """ワ: 全ノードのcounterを平均値に調和する"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            avg = sum(n.counter for n in nodes) // len(nodes)
            for n in nodes:
                n.counter = avg
            self.log(f"  ワ(harmony) → 全{len(nodes)}ノードを調和 [平均={avg}]")
        else:
            self.log(f"  ワ(harmony) → 場にノードなし（沈黙）")

    def _cmd_archive(self, token: Token) -> None:
        """ヰ: 場の状態をファイルに永続保存する"""
        snap = self.ba.snapshot()
        filename = token.label if token.label else f"ba_archive_{self.ba.tick}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
            self.log(f"  ヰ(archive) → 「{filename}」に永続保存")
        except Exception as e:
            self.log(f"  ヰ(archive) → 保存失敗: {e}")

    def _cmd_recall(self, token: Token) -> None:
        """ヱ: 保存された場の状態を復元する"""
        filename = token.label if token.label else None
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    snap = json.load(f)
                self.ba.restore_snapshot(snap)
                self.log(f"  ヱ(recall) → 「{filename}」から復元")
            except Exception as e:
                self.log(f"  ヱ(recall) → 復元失敗: {e}")
        elif self.ba.snapshots:
            snap = self.ba.snapshots[-1]
            self.ba.restore_snapshot(snap)
            self.log(f"  ヱ(recall) → 最新スナップショットから復元")
        else:
            self.log(f"  ヱ(recall) → 復元元なし（沈黙）")

    def _cmd_offer(self, token: Token) -> None:
        """ヲ: それ の値を日本語で表示する"""
        if isinstance(self.sore, Node):
            n = self.sore
            label = f"「{n.label}」" if n.label else "名なし"
            self.log(f"  ヲ(offer) → {label} の数={n.counter} 値={n.value}")
        elif self.sore is not None:
            self.log(f"  ヲ(offer) → 値: {self.sore}")
        else:
            self.log(f"  ヲ(offer) → 空（沈黙）")

    def _cmd_silence(self, token: Token) -> None:
        """ン: HALT。プログラム停止。Minskyマシンの HALT に相当。"""
        self.halt = True
        self.log(f"  ン(silence/HALT) → 停止")

    # ══════════════════════════════════════════════════
    # ─── 濁音（カ行の反転） ───
    # ══════════════════════════════════════════════════

    def _cmd_un_force(self, token: Token) -> None:
        """ガ: 力の反転 = 解放。counterを半減する"""
        if isinstance(self.sore, Node):
            self.sore.counter = self.sore.counter // 2
            self.log(f"  ガ(un_force) → {self.sore.id} を半減 [数={self.sore.counter}]")
        else:
            self.log(f"  ガ(un_force) → それ がノードでない（沈黙）")

    def _cmd_discharge(self, token: Token) -> None:
        """ギ: 充填の反転 = 放電。counterを0にリセットする"""
        if isinstance(self.sore, Node):
            self.sore.counter = 0
            self.log(f"  ギ(discharge) → {self.sore.id} を放電 [数=0]")
        else:
            self.log(f"  ギ(discharge) → それ がノードでない（沈黙）")

    def _cmd_push(self, token: Token) -> None:
        """グ: counterが最小のノードをそれ にする（引き寄せの反転）"""
        if not self.ba.nodes:
            self.log(f"  グ(push) → 場にノードなし（沈黙）")
            return
        node = min(self.ba.nodes.values(), key=lambda n: n.counter)
        self.sore = node
        self.log(f"  グ(push) → {node.id} を押し出し [数={node.counter}]")

    def _cmd_seal(self, token: Token) -> None:
        """ゲ: 放出の反転 = 封印。響バッファの先頭ノードのcounterを0にする"""
        if self.hibiki:
            sealed = self.hibiki.pop()
            if isinstance(sealed, Node) and sealed.id in self.ba.nodes:
                sealed.counter = 0
                sealed.value = "封印"
                self.log(f"  ゲ(seal) → {sealed.id} を封印 [数=0]")
            else:
                self.log(f"  ゲ(seal) → 非ノードを封印（沈黙）")
        else:
            self.log(f"  ゲ(seal) → 響バッファ空（沈黙）")

    def _cmd_surface(self, token: Token) -> None:
        """ゴ: 核の反転 = 表層。接続数が最も少ないノードをそれ にする"""
        if not self.ba.nodes:
            self.log(f"  ゴ(surface) → 場にノードなし（沈黙）")
            return
        node = min(self.ba.nodes.values(), key=lambda n: self.ba.connection_count(n.id))
        self.sore = node
        cc = self.ba.connection_count(node.id)
        self.log(f"  ゴ(surface) → {node.id} [接続数={cc}]（表層ノード）")

    # ══════════════════════════════════════════════════
    # ─── 濁音（サ行の反転） ───
    # ══════════════════════════════════════════════════

    def _cmd_unify(self, token: Token) -> None:
        """ザ: 分割の反転 = 統合。それ のノードに全ノードとのエッジを追加する"""
        if isinstance(self.sore, Node):
            added = 0
            for nid in list(self.ba.nodes.keys()):
                if nid != self.sore.id:
                    nbs = self.ba.neighbors(self.sore.id)
                    if nid not in nbs:
                        self.ba.add_edge(self.sore.id, nid)
                        added += 1
            self.log(f"  ザ(unify) → {self.sore.id} に{added}本のエッジを追加（全接続）")
        else:
            self.log(f"  ザ(unify) → それ がノードでない（沈黙）")

    def _cmd_mute(self, token: Token) -> None:
        """ジ: 信号の反転 = 沈黙信号。それ の現在counterをvalueに封じる"""
        if isinstance(self.sore, Node):
            self.sore.value = {"muted_counter": self.sore.counter, "muted_tick": self.ba.tick}
            self.log(f"  ジ(mute) → {self.sore.id} の状態を沈黙に封じた [数={self.sore.counter}]")
        else:
            self.log(f"  ジ(mute) → それ がノードでない（沈黙）")

    def _cmd_stagnate(self, token: Token) -> None:
        """ズ: 流れの反転 = 滞り。全ノードのcounterの増減を打ち消す（全て前の値に戻す）"""
        # v2.0: ズはスナップショットから前状態を復元する
        if self.ba.snapshots:
            snap = self.ba.snapshots[-1]
            for nid, data in snap.get("nodes", {}).items():
                if nid in self.ba.nodes:
                    self.ba.nodes[nid].counter = data.get("counter", 0)
            self.log(f"  ズ(stagnate) → 前スナップショットのcounterに巻き戻し")
        else:
            self.log(f"  ズ(stagnate) → スナップショットなし（沈黙）")

    def _cmd_dissociate(self, token: Token) -> None:
        """ゼ: 結合の反転 = 解離。響バッファ先頭2ノードのエッジを切断する"""
        if len(self.hibiki) >= 2:
            b = self.hibiki.pop()
            a = self.hibiki.pop()
            if isinstance(a, Node) and isinstance(b, Node):
                self.ba.remove_edge(a.id, b.id)
                self.sore = a
                self.log(f"  ゼ(dissociate) → {a.id} ─ {b.id} 解離")
            else:
                self.log(f"  ゼ(dissociate) → 非ノードの解離（沈黙）")
        else:
            self.log(f"  ゼ(dissociate) → 響バッファ不足（沈黙）")

    def _cmd_terminus(self, token: Token) -> None:
        """ゾ: 源の反転 = 終着。それ のvalueを「終着」にし、counterを0にする"""
        if isinstance(self.sore, Node):
            self.sore.value = "終着"
            self.sore.counter = 0
            self.log(f"  ゾ(terminus) → {self.sore.id} を終着点にする [数=0]")
        else:
            self.log(f"  ゾ(terminus) → それ がノードでない（沈黙）")

    # ══════════════════════════════════════════════════
    # ─── 濁音（タ行の反転） ───
    # ══════════════════════════════════════════════════

    def _cmd_unmanifest(self, token: Token) -> None:
        """ダ: 確定の反転 = 未確定。それ の値とcounterを初期状態に戻す"""
        if isinstance(self.sore, Node):
            old_value = self.sore.value
            self.sore.value = None
            self.sore.counter = 0
            self.log(f"  ダ(unmanifest) → {self.sore.id} を未確定に [旧値={old_value} 数=0]")
        else:
            self.log(f"  ダ(unmanifest) → それ がノードでない（沈黙）")

    def _cmd_scatter(self, token: Token) -> None:
        """ヂ: 凝縮の反転 = 拡散。全ノードのcounterをそれぞれ現在値の逆順に並べ替える"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            counters = [n.counter for n in nodes]
            counters.reverse()
            for n, c in zip(nodes, counters):
                n.counter = c
            self.log(f"  ヂ(scatter) → 全{len(nodes)}ノードのcounterを逆順に拡散")
        else:
            self.log(f"  ヂ(scatter) → 場にノードなし（沈黙）")

    def _cmd_unlink(self, token: Token) -> None:
        """ヅ: 束ねの反転 = 解束。響バッファの全ノードの接続を解除する"""
        count = 0
        for item in self.hibiki:
            if isinstance(item, Node) and item.id in self.ba.nodes:
                nbs = self.ba.neighbors(item.id)
                for nb_id in nbs:
                    self.ba.remove_edge(item.id, nb_id)
                count += 1
        self.log(f"  ヅ(unlink) → 響バッファ内{count}ノードの全エッジを解束")

    def _cmd_free_hand(self, token: Token) -> None:
        """デ: 指向の反転 = 解放指向。それ を響バッファに戻し、それ をNoneにする"""
        if self.sore is not None:
            self.hibiki.append(self.sore)
            name = self.sore.id if isinstance(self.sore, Node) else str(self.sore)
            self.sore = None
            self.log(f"  デ(free_hand) → {name} を響バッファに戻し、指向を解放")
        else:
            self.log(f"  デ(free_hand) → それ が空（沈黙）")

    def _cmd_separate(self, token: Token) -> None:
        """ド: 統合の反転 = 分離。全ノードのcounterを各自の birth_tick の値にリセット"""
        nodes = list(self.ba.nodes.values())
        for n in nodes:
            n.counter = n.birth_tick
        self.log(f"  ド(separate) → 全{len(nodes)}ノードのcounterをbirth_tickに分離")

    # ══════════════════════════════════════════════════
    # ─── 濁音（ハ行の反転） ───
    # ══════════════════════════════════════════════════

    def _cmd_hold_breath(self, token: Token) -> None:
        """バ: 呼吸の反転 = 息止め。全ノードのcounterを-1する（下限0）"""
        count = len(self.ba.nodes)
        for node in self.ba.nodes.values():
            node.counter = max(0, node.counter - 1)
        self.log(f"  バ(hold_breath) → 全{count}ノードの数を-1（息止め）")

    def _cmd_shadow(self, token: Token) -> None:
        """ビ: 光の反転 = 影。場の最大counterをMとして、各ノードを M - counter にする"""
        nodes = list(self.ba.nodes.values())
        if not nodes:
            self.log(f"  ビ(shadow) → 場は空（沈黙）")
            return
        M = max(n.counter for n in nodes)
        for n in nodes:
            n.counter = M - n.counter
        self.log(f"  ビ(shadow) → 全{len(nodes)}ノードのcounterを反転 [最大={M}]")

    def _cmd_converge(self, token: Token) -> None:
        """ブ: 拡散の反転 = 収束。隣接ノードのcounterをそれ に集約する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            if nbs:
                collected = 0
                for nb_id in nbs:
                    if nb_id in self.ba.nodes:
                        nb = self.ba.nodes[nb_id]
                        collected += nb.counter // 2
                        nb.counter = nb.counter - nb.counter // 2
                self.sore.counter += collected
                self.log(f"  ブ(converge) → {len(nbs)}ノードから{self.sore.id}に収束 [集約={collected}]")
            else:
                self.log(f"  ブ(converge) → 隣接ノードなし（沈黙）")
        else:
            self.log(f"  ブ(converge) → それ がノードでない（沈黙）")

    def _cmd_introvert(self, token: Token) -> None:
        """ベ: 外への反転 = 内への。counterを2倍にする（内向き蓄積）"""
        if isinstance(self.sore, Node):
            self.sore.counter *= 2
            self.log(f"  ベ(introvert) → {self.sore.id} 内向蓄積×2 [数={self.sore.counter}]")
        else:
            self.log(f"  ベ(introvert) → それ がノードでない（沈黙）")

    def _cmd_expel(self, token: Token) -> None:
        """ボ: 保持の反転 = 放出。最新スナップショットを破棄する"""
        if self.ba.snapshots:
            self.ba.snapshots.pop()
            self.log(f"  ボ(expel) → スナップショットを放出 [残り={len(self.ba.snapshots)}]")
        else:
            self.log(f"  ボ(expel) → スナップショットなし（沈黙）")

    # ══════════════════════════════════════════════════
    # ─── 半濁音（ハ行の突発操作） ───
    # ══════════════════════════════════════════════════

    def _cmd_burst(self, token: Token) -> None:
        """パ: 呼吸の突発 = 爆発。全ノードのcounterを一気に2倍にする"""
        count = len(self.ba.nodes)
        for node in self.ba.nodes.values():
            node.counter *= 2
        self.log(f"  パ(burst) → 全{count}ノードのcounterを2倍に爆発")

    def _cmd_flash(self, token: Token) -> None:
        """ピ: 光の点滅 = 瞬間。それ のcounterを場の最大+1にする（突出）"""
        if isinstance(self.sore, Node):
            if self.ba.nodes:
                mx = max(n.counter for n in self.ba.nodes.values())
                self.sore.counter = mx + 1
                self.log(f"  ピ(flash) → {self.sore.id} 瞬間突出 [数={self.sore.counter}]")
            else:
                self.sore.counter = 1
                self.log(f"  ピ(flash) → {self.sore.id} 瞬間突出 [数=1]")
        else:
            self.log(f"  ピ(flash) → それ がノードでない（沈黙）")

    def _cmd_erupt(self, token: Token) -> None:
        """プ: 拡散の噴出。それ のcounterを全ノードに均等噴出する"""
        if isinstance(self.sore, Node) and self.sore.counter > 0:
            others = [n for n in self.ba.nodes.values() if n.id != self.sore.id]
            if others:
                share = self.sore.counter // len(others)
                for n in others:
                    n.counter += share
                self.sore.counter = self.sore.counter % len(others)
                self.log(f"  プ(erupt) → {self.sore.id} から全{len(others)}ノードに噴出 [各+{share}]")
            else:
                self.log(f"  プ(erupt) → 他にノードなし（沈黙）")
        else:
            self.log(f"  プ(erupt) → それ が空かcounterゼロ（沈黙）")

    def _cmd_protrude(self, token: Token) -> None:
        """ペ: 外への突出。それ の隣接ノードとの間に中間ノードを挿入する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            inserted = 0
            for nb_id in list(nbs):
                mid = Node(
                    counter=(self.sore.counter + self.ba.nodes[nb_id].counter) // 2
                    if nb_id in self.ba.nodes else 0,
                    birth_tick=self.ba.tick,
                )
                self.ba.add_node(mid)
                self.ba.remove_edge(self.sore.id, nb_id)
                self.ba.add_edge(self.sore.id, mid.id)
                self.ba.add_edge(mid.id, nb_id)
                inserted += 1
            self.log(f"  ペ(protrude) → {self.sore.id} から{inserted}本の突出ノードを挿入")
        else:
            self.log(f"  ペ(protrude) → それ がノードでない（沈黙）")

    def _cmd_pop(self, token: Token) -> None:
        """ポ: 保持の破裂 = 解放。最新スナップショットを現在の場に合流させる"""
        if self.ba.snapshots:
            snap = self.ba.snapshots.pop()
            added = 0
            for nid, data in snap.get("nodes", {}).items():
                if nid not in self.ba.nodes:
                    node = Node(id=nid, **data)
                    self.ba.nodes[nid] = node
                    added += 1
            for edge in snap.get("edges", []):
                e = tuple(edge)
                if e not in self.ba.edges and (e[1], e[0]) not in self.ba.edges:
                    if e[0] in self.ba.nodes and e[1] in self.ba.nodes:
                        self.ba.edges.append(e)
            self.log(f"  ポ(pop) → スナップショットを破裂合流 [追加ノード={added}]")
        else:
            self.log(f"  ポ(pop) → スナップショットなし（沈黙）")


# ─── CLI ───────────────────────────────────────────

def cmd_run(source: str, verbose: bool = True) -> dict:
    paragraphs = tokenize(source)
    engine = KatakamuraEngine(verbose=verbose)
    return engine.run(paragraphs)

def cmd_exec(filepath: str, verbose: bool = True) -> dict:
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイル「{filepath}」が見つからない", file=sys.stderr)
        sys.exit(1)
    paragraphs = tokenize(source)
    engine = KatakamuraEngine(verbose=verbose)
    return engine.run(paragraphs)

def cmd_repl():
    print(f"カタカムナラング v{VERSION} REPL")
    print("終了: exit / quit / Ctrl-C")
    print("─" * 40)
    engine = KatakamuraEngine(verbose=True)
    while True:
        try:
            line = input("カタカムナ> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了")
            break
        if line.lower() in ("exit", "quit", "終了"):
            break
        if not line:
            continue
        paragraphs = tokenize(line)
        engine._build_label_table(paragraphs)
        for para in paragraphs:
            for line_tokens in para:
                for tok in line_tokens:
                    engine.ba.tick += 1
                    engine.total_ticks += 1
                    engine._execute(tok)

def print_help():
    print(f"""カタカムナラング v{VERSION}

使用法:
  python katakamuna.py run  <音素列>        音素列を直接実行
  python katakamuna.py exec <file.ktkm>     ファイルを実行
  python katakamuna.py repl                  対話モード
  python katakamuna.py list                  73音一覧
  python katakamuna.py help                  このヘルプ

環境変数:
  KATAKAMUNA_MAX_TICKS=N   N>0 でtick上限を設定（デフォルト0=無制限）

Turing完全性:
  5マクロで Minsky 2カウンタマシンをエミュレート
    INC(r)   = テ「r」カ
    DEC(r)   = テ「r」ヘ
    JZ(r,L)  = テ「r」エ「L」
    LABEL(L) = ミ「L」
    HALT     = ン
""")

def print_phoneme_table():
    print(f"{'音素':^4} {'ローマ字':^6} {'命令':^16} {'思念'}")
    print("─" * 52)
    for phoneme, info in PHONEME_TABLE.items():
        print(f"  {phoneme}   {info['romaji']:^6} {info['command']:^16} {info['shinen']}")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("help", "--help", "-h"):
        print_help()
        return
    if args[0] == "list":
        print_phoneme_table()
        return
    if args[0] == "run":
        if len(args) < 2:
            print("使用法: python katakamuna.py run <音素列>", file=sys.stderr)
            sys.exit(1)
        cmd_run(args[1])
        return
    if args[0] == "exec":
        if len(args) < 2:
            print("使用法: python katakamuna.py exec <file.ktkm>", file=sys.stderr)
            sys.exit(1)
        cmd_exec(args[1])
        return
    if args[0] == "repl":
        cmd_repl()
        return
    print(f"不明なコマンド: {args[0]}", file=sys.stderr)
    print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()
