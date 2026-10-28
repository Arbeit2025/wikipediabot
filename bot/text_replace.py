"""文字列置換の純粋ロジック。

ネットワークも Pywikibot も使わないので、単体テストで検証できる。
Bot 本体 (run_replace.py) はここで計算した結果だけを使って保存する。
"""

from __future__ import annotations

import difflib


def apply_replace(text: str, old: str, new: str) -> tuple[str, int]:
    """text 中の old をすべて new に置き換える。

    Returns:
        (置換後の文字列, 置換が起きた件数)
    """
    if old == "":
        raise ValueError("置換前の文字列 (old) が空です")
    count = text.count(old)
    if count == 0:
        return text, 0
    return text.replace(old, new), count


def make_preview(title: str, before: str, after: str, max_lines: int = 60) -> str:
    """保存せずに確認するための unified diff を作る。"""
    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"{title} (before)",
        tofile=f"{title} (after)",
        lineterm="",
    )
    lines = list(diff)
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (差分が長いため {max_lines} 行で省略)"]
    return "\n".join(lines)
