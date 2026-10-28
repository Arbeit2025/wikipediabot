"""設定ファイルの自己診断（パスワード自体は表示しない）。

ログインに失敗するとき、原因はだいたい次のどれかです。

- アカウント名の "＿" が半角 "_" になっている（正しくは全角 U+FF3F）
- BotPassword の名前が発行したものと違う
- パスワードがサンプルのまま／発行されたものと違う
- user-password.py の書式が想定と違う

このスクリプトは user-config.py と user-password.py を読み、
パスワードの「値」を見せずに、名前・文字種・長さ・書式だけを表示します。
スクリーンショットで共有しても安全です（パスワードは伏せ字になります）。

使い方:
    python -m bot.check_password_file
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

EXPECTED_USERNAME = "Whitebear＿bot"  # ＿ は全角 (U+FF3F)
PLACEHOLDER = "replace-with-the-issued-password"
SAFE_STRINGS = {"wikipedia", "ja", "pybot", "pybot2", EXPECTED_USERNAME, PLACEHOLDER}


def describe_underscore(name: str) -> str:
    parts = []
    for ch in name:
        if ch == "_":
            parts.append("半角アンダースコア U+005F（← これだと別名になります）")
        elif ch == "＿":
            parts.append("全角アンダースコア U+FF3F（正しい）")
    return "; ".join(parts) if parts else "アンダースコアなし"


def mask(value: str) -> str:
    """安全な文字列だけそのまま表示し、それ以外は伏せる。"""
    if value in SAFE_STRINGS or "Whitebear" in value:
        return repr(value)
    return f"<文字列: {len(value)}文字>"


def skeleton(node: ast.AST, depth: int = 0) -> str:
    """ファイル構造を、パスワードを伏せて表示する。"""
    pad = "  " * depth
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f"{pad}文字列 {mask(node.value)}"
        return f"{pad}{type(node.value).__name__} {node.value!r}"
    if isinstance(node, ast.Call):
        func = node.func
        fname = getattr(func, "id", None) or getattr(func, "attr", None) or "?"
        lines = [f"{pad}呼び出し {fname}(...)"]
        for arg in node.args:
            lines.append(skeleton(arg, depth + 1))
        return "\n".join(lines)
    lines = [f"{pad}{type(node).__name__}"]
    for child in ast.iter_child_nodes(node):
        lines.append(skeleton(child, depth + 1))
    return "\n".join(lines)


def read_config_username(path: Path) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str) and "Whitebear" in node.value.value:
                return node.value.value
    return None


def analyze_password_file(path: Path) -> dict:
    """書式のバリエーション（2要素/3要素タプル、属性呼び出し等）を吸収して解析する。"""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    info: dict = {"bot_call": None, "usernames": [], "skeleton": skeleton(tree)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "Whitebear" in node.value and node.value not in info["usernames"]:
                info["usernames"].append(node.value)
        if isinstance(node, ast.Call):
            func = node.func
            fname = getattr(func, "id", None) or getattr(func, "attr", None)
            if fname == "BotPassword" and len(node.args) == 2 and all(
                isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args
            ):
                info["bot_call"] = (node.args[0].value, node.args[1].value)
    return info


def main() -> int:
    root = Path.cwd()
    config_path = root / "user-config.py"
    password_path = root / "user-password.py"
    ok = True

    if not config_path.exists():
        print("NG: user-config.py がありません")
        ok = False
    else:
        name = read_config_username(config_path)
        print(f"user-config.py のアカウント名: {name!r}")
        print(f"  アンダースコア判定: {describe_underscore(name or '')}")
        if name != EXPECTED_USERNAME:
            print(f"  NG: 期待する名前 {EXPECTED_USERNAME!r} と一致しません")
            ok = False
        else:
            print("  OK: アカウント名は正しいです")

    if not password_path.exists():
        print("NG: user-password.py がありません")
        ok = False
    else:
        try:
            info = analyze_password_file(password_path)
        except SyntaxError as exc:
            print(f"NG: user-password.py が Python として読めません（{exc}）")
            info = None
            ok = False
        if info is not None:
            print(f"user-password.py 内のアカウント名候補: {info['usernames']}")
            for uname in info["usernames"]:
                print(f"  アンダースコア判定 ({uname!r}): {describe_underscore(uname)}")
                if uname != EXPECTED_USERNAME:
                    print("  NG: アカウント名が一致しません")
                    ok = False
            if info["bot_call"] is None:
                print("NG: BotPassword('名前', 'パスワード') の呼び出しが見つかりません")
                print("--- ファイル構造（パスワードは伏せ字） ---")
                print(info["skeleton"])
                print("------------------------------------------")
                ok = False
            else:
                bot_name, password = info["bot_call"]
                print(f"BotPassword の名前: {bot_name!r}（発行した名前と一致していますか？）")
                print(f"パスワード: 長さ {len(password)} 文字 / "
                      f"半角英数字のみ: {password.isascii() and password.isalnum()}")
                if password == PLACEHOLDER:
                    print("  NG: パスワードがサンプルのままです。発行されたものに書き換えてください")
                    ok = False
                elif password.strip() != password:
                    print("  NG疑い: パスワードの前後に空白が入っています")
                    ok = False
                if not info["usernames"]:
                    print("  注意: ファイル内にアカウント名の文字列が見つかりません")
                    print("--- ファイル構造（パスワードは伏せ字） ---")
                    print(info["skeleton"])
                    print("------------------------------------------")

    print("=> 名前と形式は問題なし。あとはパスワードの値そのものが正しいかだけです"
          if ok else "=> 上の NG を直してから、もう一度 python -m bot.check_site を実行してください")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
