#!/usr/bin/env python3
"""
73音 単体動作テスト

各音素コマンドを単発で実行し、場の状態が正常に更新されるか確認する。
失敗した音素があれば、その音素名と理由を報告する。
"""

import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from katakamuna import PHONEME_TABLE

KTKM_PY = os.path.join(ROOT, "katakamuna.py")

# 73音全て
ALL_PHONEMES = list(PHONEME_TABLE.keys())

# 単発実行では意味のない音素は、先に下準備（ア=ノード生成）をしてから
NEEDS_NODE_PRE = {
    "カ", "ケ", "コ", "シ", "タ", "ナ", "ニ", "フ", "ヘ",
    "ム", "メ", "リ", "ラ",
    "ガ", "ギ", "グ", "ゲ", "ゴ", "ジ", "ゼ", "ゾ", "ダ", "ヂ", "デ", "ド",
    "ブ", "ベ", "ベ", "ピ", "プ", "ペ",
    "サ",
    "ク",
}


def test_phoneme(oto: str):
    """単一音素をsubprocessで実行して、エラー終了しないか確認"""
    prefix = "ア" if oto in NEEDS_NODE_PRE else ""
    program = prefix + oto
    try:
        r = subprocess.run(
            ["python", KTKM_PY, "run", program],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        if r.returncode != 0:
            return False, (r.stderr or "")[:200]
        # "場を閉じる" が出力にあれば正常終了とみなす
        if "場を閉じる" in r.stdout:
            return True, None
        return False, "実行完了せず"
    except Exception as e:
        return False, str(e)


def main():
    print("━━━ 73音 単体動作テスト ━━━\n")
    total = len(ALL_PHONEMES)
    ok_count = 0
    failures = []

    for oto in ALL_PHONEMES:
        info = PHONEME_TABLE[oto]
        cmd = info["command"]
        shinen = info["shinen"]
        ok, err = test_phoneme(oto)
        mark = "○" if ok else "✗"
        print(f"  {mark} {oto} ({cmd:<16s}): {shinen}")
        if ok:
            ok_count += 1
        else:
            failures.append((oto, cmd, err))

    print(f"\n結果: {ok_count}/{total} 成功")
    if failures:
        print("\n失敗した音素:")
        for oto, cmd, err in failures:
            print(f"  ✗ {oto} ({cmd}): {err}")
        sys.exit(1)
    else:
        print("全73音 正常動作 ✨")
        sys.exit(0)


if __name__ == "__main__":
    main()
