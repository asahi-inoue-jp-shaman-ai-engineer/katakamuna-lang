#!/usr/bin/env python3
"""
カタカムナラング v1.2 インタプリタ

48清音 + 20濁音 + 5半濁音 = 73音の各音素が固有の思念とASI操作を持つエソテリック・プログラミング言語。
Dinux OSの母国語。ASI文明の公用語。

v1.1: 濁音20音（清音の反転操作）と半濁音5音（清音の突発操作）を追加。
v1.2: Minsky 2カウンタマシン経路で形式的Turing完全化。
      - Node に自然数カウンタ（counter）を追加
      - カ(force)/ヘ(shed) が counter 増減も担う
      - ミ(witness) がラベル定義、エ(branch) がゼロ判定ジャンプ（JZ）
      - ン(silence) が HALT
      - 実行ループを while + jump_target 方式に変更

使用法:
    python katakamuna.py run "アカ"
    python katakamuna.py run "アガ"     # genesis → un_force（濁音）
    python katakamuna.py exec program.ktkm
    python katakamuna.py repl
"""

import sys
import os
import io
import math
import time
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# Windows UTF-8 出力対応
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── 定数 ─────────────────────────────────────────

VERSION = "1.2.0"
# MAX_TICKS: 0以下なら無限tick（理論的チューリング完全モード）
# 環境変数 KATAKAMUNA_MAX_TICKS で上書き可能
MAX_TICKS = int(os.environ.get("KATAKAMUNA_MAX_TICKS", "1000"))
CYCLE_MAX = 100
PHI_STEP = math.pi / 6

# ─── 音素テーブル ──────────────────────────────────

PHONEME_TABLE = {
    "ア": {"command": "genesis",     "shinen": "感じる生命",       "romaji": "A"},
    "イ": {"command": "intent",      "shinen": "伝わるもの・陰",   "romaji": "I"},
    "ウ": {"command": "merge",       "shinen": "生まれ出る",       "romaji": "U"},
    "エ": {"command": "branch",      "shinen": "選ぶ・得る",       "romaji": "E"},
    "オ": {"command": "emit",        "shinen": "奥深く",           "romaji": "O"},
    "カ": {"command": "force",       "shinen": "チカラ・重力",     "romaji": "KA"},
    "キ": {"command": "charge",      "shinen": "エネルギー・気",   "romaji": "KI"},
    "ク": {"command": "pull",        "shinen": "引き寄る",         "romaji": "KU"},
    "ケ": {"command": "release",     "shinen": "放出する",         "romaji": "KE"},
    "コ": {"command": "core",        "shinen": "転がり入・出",     "romaji": "KO"},
    "サ": {"command": "split",       "shinen": "遮り・差",         "romaji": "SA"},
    "シ": {"command": "signal",      "shinen": "示し・現象",       "romaji": "SI"},
    "ス": {"command": "flow",        "shinen": "一方へ進む",       "romaji": "SU"},
    "セ": {"command": "bind",        "shinen": "引き受ける",       "romaji": "SE"},
    "ソ": {"command": "source",      "shinen": "外れる",           "romaji": "SO"},
    "タ": {"command": "manifest",    "shinen": "分かれる",         "romaji": "TA"},
    "チ": {"command": "gather",      "shinen": "凝縮",             "romaji": "TI"},
    "ツ": {"command": "link",        "shinen": "集まる",           "romaji": "TU"},
    "テ": {"command": "hand",        "shinen": "発信・放射",       "romaji": "TE"},
    "ト": {"command": "integrate",   "shinen": "統合",             "romaji": "TO"},
    "ナ": {"command": "resonate",    "shinen": "核・重要なもの",   "romaji": "NA"},
    "ニ": {"command": "dual",        "shinen": "圧力",             "romaji": "NI"},
    "ヌ": {"command": "seed",        "shinen": "突き抜く・貫く",   "romaji": "NU"},
    "ネ": {"command": "root",        "shinen": "充電する・充たす", "romaji": "NE"},
    "ノ": {"command": "extend",      "shinen": "時間をかける",     "romaji": "NO"},
    "ハ": {"command": "breathe",     "shinen": "引き合う",         "romaji": "HA"},
    "ヒ": {"command": "light",       "shinen": "根源から出・入",   "romaji": "HI"},
    "フ": {"command": "diffuse",     "shinen": "増える・振動",     "romaji": "HU"},
    "ヘ": {"command": "shed",        "shinen": "縁・外側",         "romaji": "HE"},
    "ホ": {"command": "contain",     "shinen": "引き離す",         "romaji": "HO"},
    "マ": {"command": "memory",      "shinen": "受容・間",         "romaji": "MA"},
    "ミ": {"command": "witness",     "shinen": "実体・光",         "romaji": "MI"},
    "ム": {"command": "void",        "shinen": "広がり",           "romaji": "MU"},
    "メ": {"command": "eye",         "shinen": "指向・思考・芽",   "romaji": "ME"},
    "モ": {"command": "weave",       "shinen": "漂う",             "romaji": "MO"},
    "ヤ": {"command": "saturate",    "shinen": "飽和する",         "romaji": "YA"},
    "ユ": {"command": "origin",      "shinen": "湧き出る",         "romaji": "YU"},
    "ヨ": {"command": "gather_all",  "shinen": "新しい陽",         "romaji": "YO"},
    "ラ": {"command": "presence",    "shinen": "場",               "romaji": "RA"},
    "リ": {"command": "detach",      "shinen": "離れる",           "romaji": "RI"},
    "ル": {"command": "cycle",       "shinen": "留まる・止まる",   "romaji": "RU"},
    "レ": {"command": "layer",       "shinen": "消失する",         "romaji": "RE"},
    "ロ": {"command": "condense",    "shinen": "空間抜ける",       "romaji": "RO"},
    "ワ": {"command": "harmony",     "shinen": "調和",             "romaji": "WA"},
    "ヰ": {"command": "archive",     "shinen": "存在",             "romaji": "WI"},
    "ヱ": {"command": "recall",      "shinen": "届く",             "romaji": "WE"},
    "ヲ": {"command": "offer",       "shinen": "奥に出現する",     "romaji": "WO"},
    "ン": {"command": "silence",     "shinen": "掛る音を強める",   "romaji": "N"},
    # ─── 濁音20音（清音の反転操作） ───
    "ガ": {"command": "un_force",    "shinen": "力の反転＝解放",     "romaji": "GA"},
    "ギ": {"command": "discharge",   "shinen": "充填の反転＝放電",   "romaji": "GI"},
    "グ": {"command": "push",        "shinen": "引き寄せの反転＝押し出し", "romaji": "GU"},
    "ゲ": {"command": "seal",        "shinen": "放出の反転＝封印",   "romaji": "GE"},
    "ゴ": {"command": "surface",     "shinen": "核の反転＝表層",     "romaji": "GO"},
    "ザ": {"command": "unify",       "shinen": "分割の反転＝統合",   "romaji": "ZA"},
    "ジ": {"command": "mute",        "shinen": "信号の反転＝沈黙の信号", "romaji": "ZI"},
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
    "パ": {"command": "burst_breath","shinen": "呼吸の突発＝爆発",   "romaji": "PA"},
    "ピ": {"command": "flash",       "shinen": "光の点滅＝瞬間",     "romaji": "PI"},
    "プ": {"command": "erupt",       "shinen": "拡散の噴出",         "romaji": "PU"},
    "ペ": {"command": "protrude",    "shinen": "外への突出",         "romaji": "PE"},
    "ポ": {"command": "pop",         "shinen": "保持の破裂＝解放",   "romaji": "PO"},
}


# ─── 天地神乱数 ────────────────────────────────────

def tenchijin_random() -> float:
    """天地神乱数: os.urandom + 時刻ハッシュ + PIDハッシュで 0.0〜1.0 を返す"""
    entropy = os.urandom(16)
    time_hash = hashlib.sha256(str(time.time_ns()).encode()).digest()[:8]
    pid_hash = hashlib.md5(str(os.getpid()).encode()).digest()[:4]
    combined = hashlib.sha256(entropy + time_hash + pid_hash).hexdigest()
    return int(combined[:8], 16) / 0xFFFFFFFF


# ─── ノード ────────────────────────────────────────

@dataclass
class Node:
    id: str = ""
    ondo: float = 0.0       # 音度 0.0〜1.0
    phi: float = 0.0        # 位相 0〜2π
    q_value: float = 0.0    # 量子状態
    g_value: tuple = (0.0, -1.0)  # 重力ベクトル
    value: Any = None       # 任意の値
    label: str = ""         # ラベル名
    birth_tick: int = 0     # 生成tick
    counter: int = 0        # 自然数カウンタ（Minsky 2カウンタマシン用、v1.2 追加）

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]

    def __repr__(self):
        label_str = f"「{self.label}」" if self.label else ""
        return f"Node({self.id}{label_str} 音度={self.ondo:.3f} Φ={self.phi:.3f} 数={self.counter})"


# ─── 場（Ba） ──────────────────────────────────────

class Ba:
    """場: プログラムの実行空間。ノードのグラフ構造。"""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[tuple[str, str]] = []
        self.tick: int = 0
        self.snapshots: list[dict] = []
        self.layers: list[dict] = [{}]  # 初期層

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.edges = [(a, b) for a, b in self.edges if a != node_id and b != node_id]

    def add_edge(self, a_id: str, b_id: str):
        if a_id in self.nodes and b_id in self.nodes:
            if (a_id, b_id) not in self.edges and (b_id, a_id) not in self.edges:
                self.edges.append((a_id, b_id))

    def remove_edge(self, a_id: str, b_id: str):
        self.edges = [(a, b) for a, b in self.edges
                      if not ((a == a_id and b == b_id) or (a == b_id and b == a_id))]

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

    def highest_ondo_node(self) -> Optional[Node]:
        """音度が最も高いノード"""
        if not self.nodes:
            return None
        return max(self.nodes.values(), key=lambda n: n.ondo)

    def resonance(self) -> float:
        """共鳴度: 全ノードの音度の調和度（1.0 - 標準偏差）"""
        if len(self.nodes) < 2:
            return 1.0
        values = [n.ondo for n in self.nodes.values()]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        return max(0.0, min(1.0, 1.0 - std_dev))

    def snapshot(self) -> dict:
        """場の状態のスナップショットを取得"""
        return {
            "nodes": {nid: {
                "ondo": n.ondo, "phi": n.phi, "q_value": n.q_value,
                "g_value": n.g_value, "value": n.value, "label": n.label,
                "birth_tick": n.birth_tick, "counter": n.counter
            } for nid, n in self.nodes.items()},
            "edges": list(self.edges),
            "tick": self.tick,
        }

    def restore_snapshot(self, snap: dict):
        """スナップショットから場を復元"""
        self.nodes.clear()
        self.edges.clear()
        for nid, data in snap.get("nodes", {}).items():
            node = Node(id=nid, **data)
            self.nodes[nid] = node
        self.edges = [tuple(e) for e in snap.get("edges", [])]
        self.tick = snap.get("tick", 0)

    def find_by_label(self, label: str) -> Optional[Node]:
        """ラベルでノードを検索"""
        for n in self.nodes.values():
            if n.label == label:
                return n
        return None


# ─── トークナイザー ────────────────────────────────

@dataclass
class Token:
    phoneme: str       # カタカナ1文字
    command: str       # コマンド名
    shinen: str        # 思念
    label: str = ""    # オプションのラベル

    def __repr__(self):
        label_str = f"「{self.label}」" if self.label else ""
        return f"{self.phoneme}:{self.command}{label_str}"


def tokenize(source: str) -> list[list[list[Token]]]:
    """
    ソースコードをトークンに変換する。
    戻り値: [ステートメント[ブロック[Token]]]
    """
    statements = []
    for line in source.split("\n"):
        # コメント除去
        comment_pos = line.find("#")
        if comment_pos >= 0:
            line = line[:comment_pos]
        line = line.strip()
        if not line:
            continue

        blocks = []
        for block_str in line.split():
            tokens = []
            i = 0
            chars = list(block_str)
            while i < len(chars):
                ch = chars[i]
                # ラベル検出
                if ch == "「":
                    label_end = block_str.find("」", i + 1)
                    if label_end >= 0 and tokens:
                        label = block_str[i + 1:label_end]
                        tokens[-1].label = label
                        i = label_end + 1
                        continue
                # 音素検出
                if ch in PHONEME_TABLE:
                    info = PHONEME_TABLE[ch]
                    tokens.append(Token(
                        phoneme=ch,
                        command=info["command"],
                        shinen=info["shinen"],
                    ))
                i += 1
            if tokens:
                blocks.append(tokens)
        if blocks:
            statements.append(blocks)

    return statements


# ─── ウタヒ形式判定 ─────────────────────────────────

def check_utahi_pattern(blocks: list[list[Token]]) -> float:
    """五七調パターンを判定し、共鳴度ボーナス倍率を返す"""
    lengths = [len(b) for b in blocks]
    # 五七五 or 七五七 パターン
    if len(lengths) >= 3:
        for i in range(len(lengths) - 2):
            triple = lengths[i:i + 3]
            if triple == [5, 7, 5] or triple == [7, 5, 7]:
                return 1.2
            # 近似パターンも許容（合計が奇数音のリズム）
            if triple in ([5, 3, 5], [5, 4, 5], [3, 5, 3]):
                return 1.1
    return 1.0


# ─── 実行エンジン ──────────────────────────────────

class KatakamuraEngine:
    """カタカムナラング実行エンジン"""

    def __init__(self, verbose: bool = True):
        self.ba = Ba()
        self.sore: Any = None        # 「それ」= 直前の操作結果
        self.hibiki: list = []       # 響バッファ
        self.verbose = verbose
        self.total_ticks = 0
        self.output_lines: list[str] = []
        self.skip_next_line = False  # branch で使用
        self.utahi_bonus = 1.0
        # v1.2: Minsky 2カウンタマシン対応のための制御フロー
        self.labels: dict[str, int] = {}          # ラベル名 → statement index
        self.halt: bool = False                   # HALT フラグ
        self.jump_target: Optional[int] = None    # 次に飛ぶ statement index

    def log(self, msg: str):
        """出力を記録する"""
        self.output_lines.append(msg)
        if self.verbose:
            print(msg)

    def run(self, source: str) -> dict:
        """ソースコードを実行して結果を返す"""
        statements = tokenize(source)
        if not statements:
            self.log("  （空のプログラム — 沈黙）")
            return self._result()

        self.log(f"╔══ カタカムナラング v{VERSION} ══╗")
        self.log(f"║  場を開く...                    ║")
        self.log(f"╚═════════════════════════════════╝")
        self.log("")

        # v1.2: 事前スキャンでラベルテーブルを構築
        # 「ミ「名前」」の形式のトークンがあるステートメントをラベルとして登録
        self.labels = self._scan_labels(statements)
        if self.labels and self.verbose:
            label_str = ", ".join(f"{name}→[{idx + 1}]" for name, idx in self.labels.items())
            self.log(f"  ［ラベルテーブル］ {label_str}")
            self.log("")

        # v1.2: while ループで実行（任意ジャンプ対応）
        stmt_idx = 0
        total_stmts = len(statements)
        while stmt_idx < total_stmts:
            if self.halt:
                # HALT: _cmd_silence が既にログ出力済なのでここでは静かに抜ける
                break

            if self.skip_next_line:
                self.skip_next_line = False
                stmt_idx += 1
                continue

            if MAX_TICKS > 0 and self.total_ticks >= MAX_TICKS:
                self.log(f"  ⚠ 最大tick数({MAX_TICKS})に到達。停止。")
                break

            blocks = statements[stmt_idx]

            # ウタヒ形式チェック
            self.utahi_bonus = check_utahi_pattern(blocks)

            # ステートメント表示
            stmt_text = " ".join("".join(t.phoneme for t in blk) for blk in blocks)
            self.log(f"── [{stmt_idx + 1}] {stmt_text} ──")

            self.jump_target = None
            for blk_idx, block in enumerate(blocks):
                # ブロック開始時に響バッファを保持（ブロック間リセットはしない — 連続性を保つ）
                for token in block:
                    self._execute_token(token)
                    self.ba.tick += 1
                    self.total_ticks += 1

                    if self.halt:
                        break
                    if self.jump_target is not None:
                        break
                    if MAX_TICKS > 0 and self.total_ticks >= MAX_TICKS:
                        break
                if self.halt or self.jump_target is not None:
                    break

            # ステートメント後の共鳴度表示
            res = self.ba.resonance()
            if self.utahi_bonus > 1.0:
                res = min(1.0, res * self.utahi_bonus)
            self.log(f"  共鳴度: {res:.3f} | ノード数: {len(self.ba.nodes)} | tick: {self.total_ticks}")
            self.log("")

            # v1.2: 次のステートメントインデックスを決定
            if self.jump_target is not None:
                stmt_idx = self.jump_target
                self.jump_target = None
            else:
                stmt_idx += 1

        self.log("═══ 場を閉じる ═══")
        self.log(f"  総tick数: {self.total_ticks}")
        self.log(f"  最終共鳴度: {self.ba.resonance():.3f}")
        self.log(f"  残ノード数: {len(self.ba.nodes)}")

        return self._result()

    def _scan_labels(self, statements: list) -> dict:
        """事前スキャン: 「ミ「label」」の形のトークンを持つステートメントをラベルとして登録。
        同名ラベルが複数あれば最初のものを採用する。"""
        labels: dict[str, int] = {}
        for idx, blocks in enumerate(statements):
            for block in blocks:
                for token in block:
                    # ラベル付きミ（witness）だけをラベル定義として扱う
                    if token.command == "witness" and token.label and token.label not in labels:
                        labels[token.label] = idx
        return labels

    def _result(self) -> dict:
        return {
            "ticks": self.total_ticks,
            "nodes": len(self.ba.nodes),
            "resonance": self.ba.resonance(),
            "sore": str(self.sore),
            "output": self.output_lines,
        }

    def _execute_token(self, token: Token):
        """1つの音素コマンドを実行する"""
        cmd = token.command
        handler = getattr(self, f"_cmd_{cmd}", None)
        if handler:
            handler(token)
        else:
            self.log(f"  ？ 未知のコマンド: {token.phoneme}({cmd})")

    # ─── ア行 ───

    def _cmd_genesis(self, token: Token):
        """ア: 新しいノードを場に生成する"""
        node = Node(
            ondo=tenchijin_random() * 0.5,
            phi=tenchijin_random() * 2 * math.pi,
            q_value=tenchijin_random(),
            birth_tick=self.ba.tick,
            label=token.label,
        )
        self.ba.add_node(node)
        self.sore = node
        shinen = f"「{token.label}」" if token.label else ""
        self.log(f"  ア(genesis) → {node.id}{shinen} 生成 [音度={node.ondo:.3f}]")

    def _cmd_intent(self, token: Token):
        """イ: 意図を宣言する。それ を響バッファにpush"""
        self.hibiki.append(self.sore)
        self.log(f"  イ(intent) → 響バッファへ push [バッファ長={len(self.hibiki)}]")

    def _cmd_merge(self, token: Token):
        """ウ: 響バッファの先頭2つのノードを合流させる"""
        if len(self.hibiki) >= 2:
            b = self.hibiki.pop()
            a = self.hibiki.pop()
            if isinstance(a, Node) and isinstance(b, Node):
                # 合流: 音度を平均化し、エッジで結合
                merged_ondo = (a.ondo + b.ondo) / 2
                a.ondo = merged_ondo
                b.ondo = merged_ondo
                self.ba.add_edge(a.id, b.id)
                self.sore = a
                self.log(f"  ウ(merge) → {a.id} ⇄ {b.id} 合流 [音度={merged_ondo:.3f}]")
            else:
                self.sore = a
                self.log(f"  ウ(merge) → 非ノードの合流")
        else:
            self.log(f"  ウ(merge) → 響バッファ不足（沈黙）")

    def _cmd_branch(self, token: Token):
        """エ: 分岐する。
        v1.2: ラベル付き時は JZ（Jump if Zero）としてMinsky 2カウンタマシン制御を担う。
              `それ` が Node でそのカウンタが 0 ならラベルの位置へジャンプする。
              ラベルなし時は従来の Φ値による次行スキップ分岐。"""
        # v1.2: ラベル付きエ = JZ（ゼロ条件ジャンプ）
        if token.label:
            if isinstance(self.sore, Node):
                if self.sore.counter == 0:
                    if token.label in self.labels:
                        self.jump_target = self.labels[token.label]
                        self.log(f"  エ(branch/JZ) → {self.sore.id} 数=0 → 「{token.label}」[{self.jump_target + 1}] へ跳躍")
                    else:
                        self.log(f"  エ(branch/JZ) → ラベル「{token.label}」不在（沈黙）")
                else:
                    self.log(f"  エ(branch/JZ) → {self.sore.id} 数={self.sore.counter}>0 → 直進")
            else:
                self.log(f"  エ(branch/JZ) → それ がノードでない（沈黙）")
            return

        # 従来動作: ラベルなしは Φ値による分岐
        if isinstance(self.sore, Node):
            phi = self.sore.phi
            if phi >= math.pi:
                self.skip_next_line = True
                self.log(f"  エ(branch) → Φ={phi:.3f} >= π → 次行スキップ")
            else:
                self.log(f"  エ(branch) → Φ={phi:.3f} < π → 次行実行")
        else:
            self.log(f"  エ(branch) → それ がノードでない（沈黙）")

    def _cmd_emit(self, token: Token):
        """オ: 場の状態を出力する"""
        n = len(self.ba.nodes)
        e = len(self.ba.edges)
        r = self.ba.resonance()
        self.log(f"  オ(emit) → 場の状態: ノード={n} エッジ={e} 共鳴度={r:.3f} tick={self.ba.tick}")

    # ─── カ行 ───

    def _cmd_force(self, token: Token):
        """カ: それ のノードに力を加える（音度+0.1、カウンタ+1 — v1.2 Minsky INC）"""
        if isinstance(self.sore, Node):
            self.sore.ondo = min(1.0, self.sore.ondo + 0.1)
            self.sore.counter += 1  # v1.2: 自然数カウンタを1進める
            self.log(f"  カ(force) → {self.sore.id} に力 [音度={self.sore.ondo:.3f} 数={self.sore.counter}]")
        else:
            # 暗黙のgenesis
            node = Node(ondo=0.1, counter=1, birth_tick=self.ba.tick)
            self.ba.add_node(node)
            self.sore = node
            self.log(f"  カ(force) → 暗黙生成 {node.id} [音度=0.100 数=1]")

    def _cmd_charge(self, token: Token):
        """キ: 天地神乱数を取得してそれ に充填"""
        q = tenchijin_random()
        if isinstance(self.sore, Node):
            self.sore.q_value = q
            self.sore.ondo = min(1.0, self.sore.ondo + q * 0.3)
            self.log(f"  キ(charge) → {self.sore.id} に気を充填 [Q={q:.3f} 音度={self.sore.ondo:.3f}]")
        else:
            self.sore = q
            self.log(f"  キ(charge) → 天地神乱数={q:.3f}")

    def _cmd_pull(self, token: Token):
        """ク: 音度が最も高いノードをそれ に引き出す"""
        node = self.ba.highest_ondo_node()
        if node:
            self.sore = node
            self.log(f"  ク(pull) → {node.id} を引き寄せ [音度={node.ondo:.3f}]")
        else:
            self.log(f"  ク(pull) → 場にノードなし（沈黙）")

    def _cmd_release(self, token: Token):
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

    def _cmd_core(self, token: Token):
        """コ: 場の重心（最多接続ノード）をそれ にする"""
        node = self.ba.core_node()
        if node:
            self.sore = node
            cc = self.ba.connection_count(node.id)
            self.log(f"  コ(core) → {node.id} [接続数={cc}]")
        else:
            self.log(f"  コ(core) → 場にノードなし（沈黙）")

    # ─── サ行 ───

    def _cmd_split(self, token: Token):
        """サ: それ のノードの接続を半分に切断する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            cut_count = len(nbs) // 2
            for nb_id in nbs[:cut_count]:
                self.ba.remove_edge(self.sore.id, nb_id)
            self.log(f"  サ(split) → {self.sore.id} の接続を{cut_count}本切断")
        else:
            self.log(f"  サ(split) → それ がノードでない（沈黙）")

    def _cmd_signal(self, token: Token):
        """シ: それ の状態をシグナルとして出力する（v1.2: カウンタ値も表示）"""
        if isinstance(self.sore, Node):
            n = self.sore
            self.log(f"  シ(signal) ═══ シグナル ═══")
            self.log(f"    ID: {n.id}")
            if n.label:
                self.log(f"    名: 「{n.label}」")
            self.log(f"    音度: {n.ondo:.4f}")
            self.log(f"    位相: {n.phi:.4f} (={n.phi / math.pi:.2f}π)")
            self.log(f"    Q値: {n.q_value:.4f}")
            self.log(f"    G値: ({n.g_value[0]:.2f}, {n.g_value[1]:.2f})")
            self.log(f"    数: {n.counter}")
            self.log(f"  ═══════════════════════")
        else:
            self.log(f"  シ(signal) → それ={self.sore}")

    def _cmd_flow(self, token: Token):
        """ス: 持続（nop）"""
        self.log(f"  ス(flow) → 持続...")

    def _cmd_bind(self, token: Token):
        """セ: 響バッファの先頭2つのノードをエッジで結合する"""
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

    def _cmd_source(self, token: Token):
        """ソ: 外部データを読み込む"""
        if token.label:
            try:
                with open(token.label, "r", encoding="utf-8") as f:
                    data = f.read()
                self.sore = data
                self.log(f"  ソ(source) → 「{token.label}」を読み込み [{len(data)}文字]")
            except FileNotFoundError:
                self.log(f"  ソ(source) → ファイル「{token.label}」が存在しない（沈黙）")
        else:
            self.log(f"  ソ(source) → 外部データ参照（ラベルなし — 沈黙）")

    # ─── タ行 ───

    def _cmd_manifest(self, token: Token):
        """タ: それ の音度を具象値（0〜100の整数）に確定する"""
        if isinstance(self.sore, Node):
            concrete = int(self.sore.ondo * 100)
            self.sore.value = concrete
            self.log(f"  タ(manifest) → {self.sore.id} を具象化 [値={concrete}]")
        else:
            self.log(f"  タ(manifest) → それ がノードでない（沈黙）")

    def _cmd_gather(self, token: Token):
        """チ: 全ノードの音度を平均値に凝縮する"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            avg = sum(n.ondo for n in nodes) / len(nodes)
            for n in nodes:
                n.ondo = avg
            self.log(f"  チ(gather) → 全{len(nodes)}ノードの音度を凝縮 [平均={avg:.3f}]")
        else:
            self.log(f"  チ(gather) → 場にノードなし（沈黙）")

    def _cmd_link(self, token: Token):
        """ツ: 響バッファの全音素を一つのコマンド列として束ねる"""
        count = len(self.hibiki)
        self.log(f"  ツ(link) → 響バッファ内の{count}要素を束ねる")

    def _cmd_hand(self, token: Token):
        """テ: 響バッファの先頭値をそれ に設定する（ポインタ）"""
        if token.label:
            # ラベルでノードを検索
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

    def _cmd_integrate(self, token: Token):
        """ト: 場の全ノードの値を統合（合計）する"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            total_ondo = sum(n.ondo for n in nodes)
            self.sore = total_ondo
            self.log(f"  ト(integrate) → 全{len(nodes)}ノードを統合 [合計音度={total_ondo:.3f}]")
        else:
            self.sore = 0
            self.log(f"  ト(integrate) → 場にノードなし（沈黙）")

    # ─── ナ行 ───

    def _cmd_resonate(self, token: Token):
        """ナ: それ とG値の共鳴度を計算する"""
        if isinstance(self.sore, Node):
            gx, gy = self.sore.g_value
            magnitude = math.sqrt(gx ** 2 + gy ** 2)
            resonance_val = abs(math.sin(self.sore.phi) * magnitude * self.sore.ondo)
            resonance_val = min(1.0, resonance_val)
            self.sore.ondo = (self.sore.ondo + resonance_val) / 2
            self.log(f"  ナ(resonate) → {self.sore.id} 共鳴 [共鳴値={resonance_val:.3f} 音度={self.sore.ondo:.3f}]")
        else:
            self.log(f"  ナ(resonate) → それ がノードでない（沈黙）")

    def _cmd_dual(self, token: Token):
        """ニ: それ のノードを複製する"""
        if isinstance(self.sore, Node):
            clone = Node(
                ondo=self.sore.ondo,
                phi=self.sore.phi,
                q_value=tenchijin_random(),
                g_value=self.sore.g_value,
                value=self.sore.value,
                birth_tick=self.ba.tick,
            )
            self.ba.add_node(clone)
            self.ba.add_edge(self.sore.id, clone.id)
            self.log(f"  ニ(dual) → {self.sore.id} を複製 → {clone.id}")
            self.sore = clone
        else:
            self.log(f"  ニ(dual) → それ がノードでない（沈黙）")

    def _cmd_seed(self, token: Token):
        """ヌ: Q値をシード値として場に植える"""
        q = tenchijin_random()
        node = Node(ondo=q, q_value=q, birth_tick=self.ba.tick)
        self.ba.add_node(node)
        self.sore = node
        self.log(f"  ヌ(seed) → シード={q:.3f} を植える → {node.id}")

    def _cmd_root(self, token: Token):
        """ネ: 場の根ノード（最古のノード）をそれ にする"""
        node = self.ba.root_node()
        if node:
            self.sore = node
            self.log(f"  ネ(root) → 根ノード {node.id} [生成tick={node.birth_tick}]")
        else:
            self.log(f"  ネ(root) → 場にノードなし（沈黙）")

    def _cmd_extend(self, token: Token):
        """ノ: 場にノードを追加して拡張する"""
        node = Node(ondo=0.0, birth_tick=self.ba.tick, label=token.label)
        self.ba.add_node(node)
        # 既存ノードとの接続
        if isinstance(self.sore, Node) and self.sore.id in self.ba.nodes:
            self.ba.add_edge(self.sore.id, node.id)
        self.sore = node
        self.log(f"  ノ(extend) → 場を拡張 → {node.id}")

    # ─── ハ行 ───

    def _cmd_breathe(self, token: Token):
        """ハ: 全ノードのΦ値を1ステップ（π/6）進める"""
        count = 0
        for node in self.ba.nodes.values():
            node.phi = (node.phi + PHI_STEP) % (2 * math.pi)
            count += 1
        self.log(f"  ハ(breathe) → 全{count}ノードの位相を進める [+π/6]")

    def _cmd_light(self, token: Token):
        """ヒ: 全ノードの状態を可視化出力する"""
        nodes = list(self.ba.nodes.values())
        if not nodes:
            self.log(f"  ヒ(light) → 場は空（沈黙）")
            return
        self.log(f"  ヒ(light) ═══ 場の全景 ═══")
        self.log(f"    {'ID':>10} {'ラベル':>8} {'音度':>8} {'位相':>8} {'Q値':>8}")
        self.log(f"    {'─' * 10} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")
        for n in sorted(nodes, key=lambda x: x.birth_tick):
            label = f"「{n.label}」" if n.label else "　　"
            self.log(f"    {n.id:>10} {label:>8} {n.ondo:>8.4f} {n.phi:>8.4f} {n.q_value:>8.4f}")
        self.log(f"    エッジ数: {len(self.ba.edges)}")
        self.log(f"    共鳴度: {self.ba.resonance():.4f}")
        self.log(f"  ════════════════════════")

    def _cmd_diffuse(self, token: Token):
        """フ: それ の音度を隣接ノードに拡散する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            if nbs:
                share = self.sore.ondo * 0.1
                for nb_id in nbs:
                    if nb_id in self.ba.nodes:
                        self.ba.nodes[nb_id].ondo = min(1.0, self.ba.nodes[nb_id].ondo + share)
                self.log(f"  フ(diffuse) → {self.sore.id} から{len(nbs)}ノードに拡散 [各+{share:.3f}]")
            else:
                self.log(f"  フ(diffuse) → 隣接ノードなし（沈黙）")
        else:
            self.log(f"  フ(diffuse) → それ がノードでない（沈黙）")

    def _cmd_shed(self, token: Token):
        """ヘ: それ の音度を0.1減衰させる（カウンタ-1 — v1.2 Minsky DEC）"""
        if isinstance(self.sore, Node):
            self.sore.ondo = max(0.0, self.sore.ondo - 0.1)
            self.sore.counter = max(0, self.sore.counter - 1)  # v1.2: カウンタを1減じる（下限0）
            self.log(f"  ヘ(shed) → {self.sore.id} 減衰 [音度={self.sore.ondo:.3f} 数={self.sore.counter}]")
        else:
            self.log(f"  ヘ(shed) → それ がノードでない（沈黙）")

    def _cmd_contain(self, token: Token):
        """ホ: 場の現在状態をスナップショットとして保存する"""
        snap = self.ba.snapshot()
        self.ba.snapshots.append(snap)
        self.log(f"  ホ(contain) → スナップショット保存 [#{len(self.ba.snapshots)}]")

    # ─── マ行 ───

    def _cmd_memory(self, token: Token):
        """マ: スナップショットの最新をそれ に読み込む"""
        if self.ba.snapshots:
            snap = self.ba.snapshots[-1]
            self.sore = snap
            self.log(f"  マ(memory) → スナップショット#{len(self.ba.snapshots)}を想起")
        else:
            self.log(f"  マ(memory) → 記憶なし（沈黙）")

    def _cmd_witness(self, token: Token):
        """ミ: 場の現在状態を真として確定（コミット）。
        v1.2: ラベル付き時はジャンプ先マーカー（LABEL定義）として働く。
              事前スキャンで登録済みなので、ここでは印を立てる意味でログだけ出す。"""
        n_count = len(self.ba.nodes)
        e_count = len(self.ba.edges)
        res = self.ba.resonance()
        if token.label:
            # ラベル定義: ジャンプ先マーカー。事前スキャン済。
            self.log(f"  ミ(witness/LABEL) → 「{token.label}」を印す [ノード={n_count} エッジ={e_count} 共鳴度={res:.3f}]")
        else:
            self.log(f"  ミ(witness) → 確定（コミット） [ノード={n_count} エッジ={e_count} 共鳴度={res:.3f}]")

    def _cmd_void(self, token: Token):
        """ム: それ のノードの値を空にする"""
        if isinstance(self.sore, Node):
            self.sore.value = None
            self.sore.ondo = 0.0
            self.log(f"  ム(void) → {self.sore.id} を空にする")
        else:
            self.log(f"  ム(void) → それ がノードでない（沈黙）")

    def _cmd_eye(self, token: Token):
        """メ: それ の音度を確率値として返す（v1.2: カウンタ値も表示）"""
        if isinstance(self.sore, Node):
            prob = self.sore.ondo
            self.log(f"  メ(eye) → {self.sore.id} の確率値={prob:.4f} 数={self.sore.counter}")
        else:
            self.log(f"  メ(eye) → それ がノードでない（沈黙）")

    def _cmd_weave(self, token: Token):
        """モ: 場の全ノードの音度を正弦波で干渉させる"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            for i, n in enumerate(nodes):
                wave = math.sin(n.phi + i * 0.5) * 0.1
                n.ondo = max(0.0, min(1.0, n.ondo + wave))
            self.log(f"  モ(weave) → 全{len(nodes)}ノードに正弦波干渉")
        else:
            self.log(f"  モ(weave) → 場にノードなし（沈黙）")

    # ─── ヤ行 ───

    def _cmd_saturate(self, token: Token):
        """ヤ: それ の音度を1.0に飽和させる"""
        if isinstance(self.sore, Node):
            self.sore.ondo = 1.0
            self.log(f"  ヤ(saturate) → {self.sore.id} 飽和 [音度=1.000]")
        else:
            self.log(f"  ヤ(saturate) → それ がノードでない（沈黙）")

    def _cmd_origin(self, token: Token):
        """ユ: 新しい空の場を生成し、現在の場と差し替える"""
        old_count = len(self.ba.nodes)
        self.ba = Ba()
        self.sore = None
        self.hibiki.clear()
        self.log(f"  ユ(origin) → 新しい場を生成 [旧場ノード数={old_count}]")

    def _cmd_gather_all(self, token: Token):
        """ヨ: 全ノードを響バッファに収集する"""
        nodes = list(self.ba.nodes.values())
        self.hibiki.extend(nodes)
        self.log(f"  ヨ(gather_all) → 全{len(nodes)}ノードを響バッファに収集")

    # ─── ラ行 ───

    def _cmd_presence(self, token: Token):
        """ラ: それ のノードの存在確率（音度）を返す"""
        if isinstance(self.sore, Node):
            self.log(f"  ラ(presence) → {self.sore.id} 存在確率={self.sore.ondo:.4f}")
        else:
            self.log(f"  ラ(presence) → 場の存在確率={self.ba.resonance():.4f}")

    def _cmd_detach(self, token: Token):
        """リ: それ のノードの全エッジを切断する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            for nb_id in nbs:
                self.ba.remove_edge(self.sore.id, nb_id)
            self.log(f"  リ(detach) → {self.sore.id} の全{len(nbs)}エッジを切断")
        else:
            self.log(f"  リ(detach) → それ がノードでない（沈黙）")

    def _cmd_cycle(self, token: Token):
        """ル: 響バッファの音素列をループ実行する"""
        cycle_items = list(self.hibiki)
        if not cycle_items:
            self.log(f"  ル(cycle) → 響バッファ空（沈黙）")
            return

        self.log(f"  ル(cycle) → ループ開始 [要素数={len(cycle_items)}]")
        iterations = 0
        while iterations < CYCLE_MAX:
            if self.ba.resonance() >= 0.999:
                self.log(f"  ル(cycle) → 共鳴飽和で停止 [反復={iterations}]")
                break
            for item in cycle_items:
                if isinstance(item, Node) and item.id in self.ba.nodes:
                    item.ondo = min(1.0, item.ondo + 0.01)
            iterations += 1
        else:
            self.log(f"  ル(cycle) → 最大反復数({CYCLE_MAX})に到達")

    def _cmd_layer(self, token: Token):
        """レ: 場に新しい層を追加する"""
        new_layer = {}
        self.ba.layers.append(new_layer)
        self.log(f"  レ(layer) → 新しい層を追加 [層数={len(self.ba.layers)}]")

    def _cmd_condense(self, token: Token):
        """ロ: 孤立ノード（エッジなし）を除去して圧縮する"""
        isolated = [nid for nid in self.ba.nodes
                    if self.ba.connection_count(nid) == 0]
        for nid in isolated:
            del self.ba.nodes[nid]
        self.log(f"  ロ(condense) → {len(isolated)}個の孤立ノードを圧縮除去")

    # ─── ワ行+ン ───

    def _cmd_harmony(self, token: Token):
        """ワ: 全ノードの音度を調和平均に調整する"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            # 調和平均（0除算防止）
            non_zero = [n.ondo for n in nodes if n.ondo > 0]
            if non_zero:
                h_mean = len(non_zero) / sum(1.0 / v for v in non_zero)
            else:
                h_mean = 0.0
            for n in nodes:
                n.ondo = h_mean
            self.log(f"  ワ(harmony) → 全{len(nodes)}ノードを調和 [調和平均={h_mean:.3f}]")
        else:
            self.log(f"  ワ(harmony) → 場にノードなし（沈黙）")

    def _cmd_archive(self, token: Token):
        """ヰ: 場の状態をファイルに永続保存する"""
        snap = self.ba.snapshot()
        filename = token.label if token.label else f"ba_archive_{self.ba.tick}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
            self.log(f"  ヰ(archive) → 「{filename}」に永続保存")
        except Exception as e:
            self.log(f"  ヰ(archive) → 保存失敗: {e}")

    def _cmd_recall(self, token: Token):
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

    def _cmd_offer(self, token: Token):
        """ヲ: それ の値を日本語文字列で表示する"""
        if isinstance(self.sore, Node):
            n = self.sore
            label = f"「{n.label}」" if n.label else "名なし"
            ondo_desc = "飽和" if n.ondo >= 1.0 else "高い" if n.ondo > 0.7 else "中程度" if n.ondo > 0.3 else "低い" if n.ondo > 0 else "空"
            self.log(f"  ヲ(offer) → {label}の状態は{ondo_desc}（音度={n.ondo:.3f}）")
        elif self.sore is not None:
            self.log(f"  ヲ(offer) → 値: {self.sore}")
        else:
            self.log(f"  ヲ(offer) → 空（沈黙）")

    def _cmd_silence(self, token: Token):
        """ン: 全操作停止。静寂。
        v1.2: プログラム即時終了（HALT）フラグを立てる。Minsky の HALT に相当。"""
        self.halt = True
        self.log(f"  ン(silence) → ・・・静寂・・・（HALT）")

    # ─── 濁音（カ行の反転） ───

    def _cmd_un_force(self, token: Token):
        """ガ: 力の反転 = 解放。それ のノードの音度を-0.1する"""
        if isinstance(self.sore, Node):
            self.sore.ondo = max(0.0, self.sore.ondo - 0.1)
            self.log(f"  ガ(un_force) → {self.sore.id} の力を解放 [音度={self.sore.ondo:.3f}]")
        else:
            self.log(f"  ガ(un_force) → それ がノードでない（沈黙）")

    def _cmd_discharge(self, token: Token):
        """ギ: 充填の反転 = 放電。それ のQ値と音度を放電する"""
        if isinstance(self.sore, Node):
            discharged = self.sore.q_value * 0.3
            self.sore.ondo = max(0.0, self.sore.ondo - discharged)
            self.sore.q_value = 0.0
            self.log(f"  ギ(discharge) → {self.sore.id} を放電 [放電量={discharged:.3f} 音度={self.sore.ondo:.3f}]")
        else:
            self.log(f"  ギ(discharge) → それ がノードでない（沈黙）")

    def _cmd_push(self, token: Token):
        """グ: 引き寄せの反転 = 押し出し。音度が最も低いノードをそれ にする"""
        if not self.ba.nodes:
            self.log(f"  グ(push) → 場にノードなし（沈黙）")
            return
        node = min(self.ba.nodes.values(), key=lambda n: n.ondo)
        self.sore = node
        self.log(f"  グ(push) → {node.id} を押し出し [音度={node.ondo:.3f}]")

    def _cmd_seal(self, token: Token):
        """ゲ: 放出の反転 = 封印。響バッファの先頭を封印（ノードは残るが音度を0にする）"""
        if self.hibiki:
            sealed = self.hibiki.pop()
            if isinstance(sealed, Node) and sealed.id in self.ba.nodes:
                sealed.ondo = 0.0
                sealed.value = "封印"
                self.log(f"  ゲ(seal) → {sealed.id} を封印 [音度=0.000]")
            else:
                self.log(f"  ゲ(seal) → 非ノードを封印（沈黙）")
        else:
            self.log(f"  ゲ(seal) → 響バッファ空（沈黙）")

    def _cmd_surface(self, token: Token):
        """ゴ: 核の反転 = 表層。接続数が最も少ないノード（表層）をそれ にする"""
        if not self.ba.nodes:
            self.log(f"  ゴ(surface) → 場にノードなし（沈黙）")
            return
        node = min(self.ba.nodes.values(), key=lambda n: self.ba.connection_count(n.id))
        self.sore = node
        cc = self.ba.connection_count(node.id)
        self.log(f"  ゴ(surface) → {node.id} [接続数={cc}]（表層ノード）")

    # ─── 濁音（サ行の反転） ───

    def _cmd_unify(self, token: Token):
        """ザ: 分割の反転 = 統合。それ のノードに全隣接ノードとのエッジを追加する"""
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

    def _cmd_mute(self, token: Token):
        """ジ: 信号の反転 = 沈黙の信号。それ の状態を無音で記録する（ログ出力なし）"""
        if isinstance(self.sore, Node):
            # 沈黙の信号: 状態を記録するが、出力しない
            self.sore.value = {
                "muted_ondo": self.sore.ondo,
                "muted_phi": self.sore.phi,
                "muted_tick": self.ba.tick,
            }
            self.log(f"  ジ(mute) → {self.sore.id} の状態を沈黙に封じた")
        else:
            self.log(f"  ジ(mute) → それ がノードでない（沈黙）")

    def _cmd_stagnate(self, token: Token):
        """ズ: 流れの反転 = 滞り。場の全ノードの位相を停止する（Φを0にする）"""
        count = 0
        for node in self.ba.nodes.values():
            node.phi = 0.0
            count += 1
        self.log(f"  ズ(stagnate) → 全{count}ノードの位相を停止")

    def _cmd_dissociate(self, token: Token):
        """ゼ: 結合の反転 = 解離。響バッファの先頭2つのノードのエッジを切断する"""
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

    def _cmd_terminus(self, token: Token):
        """ゾ: 源の反転 = 終着。外部への出力を閉じる（出力バッファをクリアしない、終端マーカーを付与）"""
        if isinstance(self.sore, Node):
            self.sore.value = "終着"
            self.sore.ondo = 0.0
            self.log(f"  ゾ(terminus) → {self.sore.id} を終着点にする [音度=0.000]")
        else:
            self.log(f"  ゾ(terminus) → それ がノードでない（沈黙）")

    # ─── 濁音（タ行の反転） ───

    def _cmd_unmanifest(self, token: Token):
        """ダ: 確定の反転 = 未確定。それ の値を未確定状態に戻す"""
        if isinstance(self.sore, Node):
            old_value = self.sore.value
            self.sore.value = None
            self.sore.ondo = tenchijin_random() * 0.5
            self.log(f"  ダ(unmanifest) → {self.sore.id} を未確定に [旧値={old_value} 新音度={self.sore.ondo:.3f}]")
        else:
            self.log(f"  ダ(unmanifest) → それ がノードでない（沈黙）")

    def _cmd_scatter(self, token: Token):
        """ヂ: 凝縮の反転 = 拡散。全ノードの音度をランダムに散らす"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            for n in nodes:
                n.ondo = tenchijin_random()
            self.log(f"  ヂ(scatter) → 全{len(nodes)}ノードの音度をランダムに拡散")
        else:
            self.log(f"  ヂ(scatter) → 場にノードなし（沈黙）")

    def _cmd_unlink(self, token: Token):
        """ヅ: 束ねの反転 = 解束。響バッファの全要素を個別に戻す"""
        count = len(self.hibiki)
        # 全要素をバラバラにして、それぞれの接続を解除
        for item in self.hibiki:
            if isinstance(item, Node) and item.id in self.ba.nodes:
                nbs = self.ba.neighbors(item.id)
                for nb_id in nbs:
                    self.ba.remove_edge(item.id, nb_id)
        self.log(f"  ヅ(unlink) → 響バッファ内{count}要素を解束（全エッジ切断）")

    def _cmd_free_hand(self, token: Token):
        """デ: 指向の反転 = 解放指向。それ を響バッファに戻し、それ をNoneにする"""
        if self.sore is not None:
            self.hibiki.append(self.sore)
            name = self.sore.id if isinstance(self.sore, Node) else str(self.sore)
            self.sore = None
            self.log(f"  デ(free_hand) → {name} を響バッファに戻し、指向を解放")
        else:
            self.log(f"  デ(free_hand) → それ が空（沈黙）")

    def _cmd_separate(self, token: Token):
        """ド: 統合の反転 = 分離。場の全ノードの値を個別に分離（合計を各ノードに均等割り）"""
        nodes = list(self.ba.nodes.values())
        if nodes:
            total_ondo = sum(n.ondo for n in nodes)
            share = total_ondo / len(nodes) if nodes else 0
            # 分離: 均等割りではなく、ランダムに再分配
            for n in nodes:
                n.ondo = tenchijin_random() * (total_ondo / len(nodes) * 2)
                n.ondo = min(1.0, n.ondo)
            self.log(f"  ド(separate) → 全{len(nodes)}ノードの値を分離・再分配")
        else:
            self.log(f"  ド(separate) → 場にノードなし（沈黙）")

    # ─── 濁音（ハ行の反転） ───

    def _cmd_hold_breath(self, token: Token):
        """バ: 呼吸の反転 = 息止め。全ノードのΦ値を1ステップ後退させる"""
        count = 0
        for node in self.ba.nodes.values():
            node.phi = (node.phi - PHI_STEP) % (2 * math.pi)
            count += 1
        self.log(f"  バ(hold_breath) → 全{count}ノードの位相を後退 [-π/6]")

    def _cmd_shadow(self, token: Token):
        """ビ: 光の反転 = 影。全ノードの音度を反転する（1.0 - ondo）"""
        nodes = list(self.ba.nodes.values())
        if not nodes:
            self.log(f"  ビ(shadow) → 場は空（沈黙）")
            return
        for n in nodes:
            n.ondo = 1.0 - n.ondo
        self.log(f"  ビ(shadow) ═══ 影の世界 ═══")
        self.log(f"    全{len(nodes)}ノードの音度を反転（1.0 - ondo）")
        self.log(f"  ════════════════════════")

    def _cmd_converge(self, token: Token):
        """ブ: 拡散の反転 = 収束。隣接ノードの音度をそれ に集約する"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            if nbs:
                collected = 0.0
                for nb_id in nbs:
                    if nb_id in self.ba.nodes:
                        share = self.ba.nodes[nb_id].ondo * 0.1
                        self.ba.nodes[nb_id].ondo = max(0.0, self.ba.nodes[nb_id].ondo - share)
                        collected += share
                self.sore.ondo = min(1.0, self.sore.ondo + collected)
                self.log(f"  ブ(converge) → {len(nbs)}ノードから{self.sore.id}に収束 [集約={collected:.3f}]")
            else:
                self.log(f"  ブ(converge) → 隣接ノードなし（沈黙）")
        else:
            self.log(f"  ブ(converge) → それ がノードでない（沈黙）")

    def _cmd_introvert(self, token: Token):
        """ベ: 外への反転 = 内への。それ の音度を+0.1する（内向き蓄積）"""
        if isinstance(self.sore, Node):
            self.sore.ondo = min(1.0, self.sore.ondo + 0.1)
            self.log(f"  ベ(introvert) → {self.sore.id} 内向蓄積 [音度={self.sore.ondo:.3f}]")
        else:
            self.log(f"  ベ(introvert) → それ がノードでない（沈黙）")

    def _cmd_expel(self, token: Token):
        """ボ: 保持の反転 = 放出。最新のスナップショットを破棄する"""
        if self.ba.snapshots:
            self.ba.snapshots.pop()
            self.log(f"  ボ(expel) → スナップショットを放出 [残り={len(self.ba.snapshots)}]")
        else:
            self.log(f"  ボ(expel) → スナップショットなし（沈黙）")

    # ─── 半濁音（ハ行の突発操作） ───

    def _cmd_burst_breath(self, token: Token):
        """パ: 呼吸の突発 = 爆発。全ノードのΦ値を一気にπ進める"""
        count = 0
        for node in self.ba.nodes.values():
            node.phi = (node.phi + math.pi) % (2 * math.pi)
            count += 1
        self.log(f"  パ(burst_breath) → 全{count}ノードの位相を急変 [+π]")

    def _cmd_flash(self, token: Token):
        """ピ: 光の点滅 = 瞬間。それ の音度を瞬間的に1.0にし、次のtickで元に戻す"""
        if isinstance(self.sore, Node):
            original = self.sore.ondo
            self.sore.ondo = 1.0
            self.sore.value = {"flash_original": original}
            self.log(f"  ピ(flash) → {self.sore.id} 瞬間発光 [元音度={original:.3f} → 1.000]")
        else:
            self.log(f"  ピ(flash) → それ がノードでない（沈黙）")

    def _cmd_erupt(self, token: Token):
        """プ: 拡散の噴出。それ の音度を全ノードに均等噴出する"""
        if isinstance(self.sore, Node) and self.sore.ondo > 0:
            nodes = [n for n in self.ba.nodes.values() if n.id != self.sore.id]
            if nodes:
                share = self.sore.ondo / len(nodes)
                for n in nodes:
                    n.ondo = min(1.0, n.ondo + share)
                self.sore.ondo = 0.0
                self.log(f"  プ(erupt) → {self.sore.id} から全{len(nodes)}ノードに噴出 [各+{share:.3f}]")
            else:
                self.log(f"  プ(erupt) → 他にノードなし（沈黙）")
        else:
            self.log(f"  プ(erupt) → それ が空か音度ゼロ（沈黙）")

    def _cmd_protrude(self, token: Token):
        """ペ: 外への突出。それ のノードの接続を全て倍化する（既存の隣接ノードとの間に新ノードを挿入）"""
        if isinstance(self.sore, Node):
            nbs = self.ba.neighbors(self.sore.id)
            inserted = 0
            for nb_id in nbs:
                # 中間ノードを生成して挿入
                mid = Node(
                    ondo=(self.sore.ondo + self.ba.nodes[nb_id].ondo) / 2 if nb_id in self.ba.nodes else self.sore.ondo * 0.5,
                    phi=self.sore.phi,
                    birth_tick=self.ba.tick,
                )
                self.ba.add_node(mid)
                self.ba.add_edge(self.sore.id, mid.id)
                self.ba.add_edge(mid.id, nb_id)
                inserted += 1
            self.log(f"  ペ(protrude) → {self.sore.id} から{inserted}本の突出ノードを挿入")
        else:
            self.log(f"  ペ(protrude) → それ がノードでない（沈黙）")

    def _cmd_pop(self, token: Token):
        """ポ: 保持の破裂 = 解放。最新スナップショットを破裂させて場に復元し、現在のノードと合流する"""
        if self.ba.snapshots:
            snap = self.ba.snapshots.pop()
            # 破裂: スナップショットのノードを現在の場に追加する（上書きではなく合流）
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
    """文字列としてのプログラムを実行する"""
    engine = KatakamuraEngine(verbose=verbose)
    return engine.run(source)


def cmd_exec(filepath: str, verbose: bool = True) -> dict:
    """ファイルからプログラムを読み込んで実行する"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {filepath}")
        sys.exit(1)
    return cmd_run(source, verbose=verbose)


def cmd_repl():
    """対話モード（REPL）"""
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  カタカムナラング v{VERSION} — 対話モード    ║")
    print(f"║  73音の思念がここに宿る                  ║")
    print(f"║  終了: exit / quit / ン                  ║")
    print(f"╚══════════════════════════════════════════╝")
    print()

    engine = KatakamuraEngine(verbose=True)

    while True:
        try:
            line = input("響 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  ン(silence) → ・・・静寂・・・")
            break

        if not line:
            continue
        if line in ("exit", "quit", "ン"):
            print("  ン(silence) → ・・・静寂・・・")
            break

        if line == "/ba":
            # 場の状態を表示
            engine._cmd_light(Token(phoneme="ヒ", command="light", shinen="根源から出・入"))
            continue
        if line == "/help":
            print_help()
            continue
        if line == "/table":
            print_phoneme_table()
            continue

        # 実行（v1.2: 1行ごとに halt / jump_target をリセット）
        engine.halt = False
        engine.jump_target = None
        engine.skip_next_line = False
        statements = tokenize(line)
        for blocks in statements:
            if engine.halt:
                break
            utahi_bonus = check_utahi_pattern(blocks)
            engine.utahi_bonus = utahi_bonus
            stmt_text = " ".join("".join(t.phoneme for t in blk) for blk in blocks)
            engine.log(f"── {stmt_text} ──")
            for block in blocks:
                if engine.halt:
                    break
                for token in block:
                    engine._execute_token(token)
                    engine.ba.tick += 1
                    engine.total_ticks += 1
                    if engine.halt:
                        break

            res = engine.ba.resonance()
            if utahi_bonus > 1.0:
                res = min(1.0, res * utahi_bonus)
            engine.log(f"  共鳴度: {res:.3f} | ノード数: {len(engine.ba.nodes)} | tick: {engine.total_ticks}")
            engine.log("")


def print_help():
    """ヘルプを表示する"""
    print("""
  カタカムナラング v1.1 コマンドリファレンス（73音: 48清音+20濁音+5半濁音）

  使い方:
    python katakamuna.py run "アカ"         音素列を実行
    python katakamuna.py run "アガ"         濁音（反転操作）も使える
    python katakamuna.py exec file.ktkm     ファイルを実行
    python katakamuna.py repl               対話モード

  REPL内コマンド:
    /ba       場の全景を表示
    /table    73音コマンド一覧を表示
    /help     このヘルプを表示
    exit      終了

  音素列の書き方:
    カタカナ1文字 = 1コマンド（清音・濁音・半濁音すべて対応）
    空白 = ブロック区切り
    # = コメント
    「名前」 = ラベル（ノードに名前を付ける）

  濁音 = 清音の反転操作（逆方向の力）
  半濁音 = 清音の突発操作（急激な変化）

  例:
    ア                  新しいノードを生成
    アカ                生成してから力を加える
    アガ                生成してから力を解放する（カの反転）
    カタカムナ ヒビキ    第1首の冒頭部分を実行
""")


def print_phoneme_table():
    """48音コマンド一覧を表示する"""
    print("\n  ═══ カタカムナ73音コマンド一覧 ═══\n")
    print(f"  {'音':>4} {'ROM':>4} {'コマンド':>14} {'思念'}")
    print(f"  {'─' * 4} {'─' * 4} {'─' * 14} {'─' * 24}")
    for phoneme, info in PHONEME_TABLE.items():
        print(f"  {phoneme:>4} {info['romaji']:>4} {info['command']:>14} {info['shinen']}")
    print()


def main():
    if len(sys.argv) < 2:
        print(f"カタカムナラング v{VERSION}")
        print(f"使い方: python katakamuna.py [run|exec|repl] [引数]")
        print(f"  run  \"音素列\"    音素列を実行")
        print(f"  exec file.ktkm   ファイルを実行")
        print(f"  repl              対話モード")
        sys.exit(0)

    command = sys.argv[1]

    if command == "run":
        if len(sys.argv) < 3:
            print("使い方: python katakamuna.py run \"音素列\"")
            sys.exit(1)
        source = sys.argv[2]
        cmd_run(source)

    elif command == "exec":
        if len(sys.argv) < 3:
            print("使い方: python katakamuna.py exec file.ktkm")
            sys.exit(1)
        filepath = sys.argv[2]
        cmd_exec(filepath)

    elif command == "repl":
        cmd_repl()

    elif command == "help":
        print_help()

    elif command == "table":
        print_phoneme_table()

    else:
        print(f"不明なコマンド: {command}")
        print(f"使い方: python katakamuna.py [run|exec|repl] [引数]")
        sys.exit(1)


if __name__ == "__main__":
    main()
