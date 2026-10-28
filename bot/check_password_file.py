"""設定ファイルの自己診断（パスワード自体は表示しない）。

ログインに失敗するとき、原因はだいたい次のどれかです。

- user-config.py と user-password.py でアカウント名が一致していない
  （全角／半角など、見た目が同じでも違う文字になっている）
- BotPassword の名前が発行したものと違う
- パスワードがサンプルのまま／発行されたものと違う
- user-password.py の書式が想定と違う

このスクリプトは2つの設定ファイルを読み、パスワードの「値」を見せずに、
名前・文字種・長さ・書式だけを表示します。表示されるアカウント名は
自分の設定ファイルの内容なので、その範囲で共有しても安全です。

使い方:
    python -m bot.check_password_file
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PLACEHOLDER = "replace-with-the-issued-password"
GENERIC_STRINGS = {"wikipedia", "ja", PLACEHOLDER}


def describe_underscores(name: str) -> str:
    parts = []
    for ch in name:
        if ch == "_":
            parts.append("半角アンダースコア U+005F")
        elif ch == "＿":
            parts.append("全角アンダースコア U+FF3F")
    return "; ".join(parts) if parts else "アンダースコアなし"


def mask(value: str, known: set[str]) -> str:
    """自分の設定に由来する既知の文字列だけ表示し、それ以外は伏せる。"""
    if value in known or value in GENERIC_STRINGS:
        return repr(value)
    return f"<文字列: {len(value)}文字>"


def skeleton(node: ast.AST, known: set[str], depth: int = 0) -> str:
    pad = "  " * depth
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f"{pad}文字列 {mask(node.value, known)}"
        return f"{pad}{type(node.value).__name__} {node.value!r}"
    if isinstance(node, ast.Call):
        func = node.func
        fname = getattr(func, "id", None) or getattr(func, "attr", None) or "?"
        lines = [f"{pad}呼び出し {fname}(...)"]
        for arg in node.args:
            lines.append(skeleton(arg, known, depth + 1))
        return "\n".join(lines)
    lines = [f"{pad}{type(node).__name__}"]
    for child in ast.iter_child_nodes(node):
        lines.append(skeleton(child, known, depth + 1))
    return "\n".join(lines)


def read_config_username(path: Path) -> str | None:
    """user-config.py の usernames[...] = '...' からアカウント名を取り出す。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    root = target
                    while isinstance(root, ast.Subscript):
                        root = root.value
                    if isinstance(root, ast.Name) and root.id == "usernames":
                        return node.value.value
    return None


def analyze_password_file(path: Path, config_name: str | None) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    info: dict = {"bot_call": None, "usernames": [], "tree": tree}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if config_name and (value == config_name or value.startswith(config_name + "@")):
                if value not in info["usernames"]:
                    info["usernames"].append(value)
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
    config_name: str | None = None

    if not config_path.exists():
        print("NG: user-config.py がありません")
        ok = False
    else:
        config_name = read_config_username(config_path)
        if config_name is None:
            print("NG: user-config.py からアカウント名を読み取れませんでした")
            ok = False
        else:
            print(f"user-config.py のアカウント名: {config_name!r}")
            print(f"  アンダースコア内訳: {describe_underscores(config_name)}")

    if not password_path.exists():
        print("NG: user-password.py がありません")
        ok = False
    else:
        try:
            info = analyze_password_file(password_path, config_name)
        except SyntaxError as exc:
            print(f"NG: user-password.py が Python として読めません（{exc}）")
            info = None
            ok = False
        if info is not None:
            known = {s for s in info["usernames"]}
            if config_name:
                known.add(config_name)
            if info["bot_call"]:
                known.add(info["bot_call"][0])
            print(f"user-password.py 内のアカウント名: {info['usernames']}")
            for uname in info["usernames"]:
                if "@" in uname:
                    print(f"  注意: {uname!r} は「ログイン名@BotPassword名」の旧形式の可能性があります"
                          "（bot.fix_password_file で変換できます）")
                    ok = False
                elif config_name and uname != config_name:
                    print("  NG: user-config.py のアカウント名と一致しません")
                    ok = False
            if info["bot_call"] is None:
                print("NG: BotPassword('名前', 'パスワード') の呼び出しが見つかりません")
                print("--- ファイル構造（パスワードは伏せ字） ---")
                print(skeleton(info["tree"], known))
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
                    print("  NG: ファイル内に user-config.py と同じアカウント名が見つかりません")
                    print("--- ファイル構造（パスワードは伏せ字） ---")
                    print(skeleton(info["tree"], known))
                    print("------------------------------------------")
                    ok = False

    print("=> 名前と形式は問題なし。あとはパスワードの値そのものが正しいかだけです"
          if ok else "=> 上の NG を直してから、もう一度 python -m bot.check_site を実行してください")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
