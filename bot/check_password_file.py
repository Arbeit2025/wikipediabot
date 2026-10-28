"""設定ファイルの自己診断（パスワード自体は表示しない）。

ログインに失敗するとき、原因はだいたい次のどれかです。

- アカウント名の "＿" が半角 "_" になっている（正しくは全角 U+FF3F）
- BotPassword の名前が発行したものと違う
- パスワードがサンプルのまま／発行されたものと違う

このスクリプトは user-config.py と user-password.py を読み、
パスワードの「値」を見せずに、名前・文字種・長さだけを表示します。
スクリーンショットで共有しても安全です（パスワードは出ません）。

使い方:
    python -m bot.check_password_file
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

EXPECTED_USERNAME = "YourBotName"  # ＿ は全角 (U+FF3F)
PLACEHOLDER = "replace-with-the-issued-password"


def describe_underscore(name: str) -> str:
    parts = []
    for ch in name:
        if ch == "_":
            parts.append("半角アンダースコア U+005F（← これだと別名になります）")
        elif ch == "＿":
            parts.append("全角アンダースコア U+FF3F（正しい）")
    return "; ".join(parts) if parts else "アンダースコアなし"


def read_config_username(path: Path) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str) and "YourBot" in node.value.value:
                return node.value.value
    return None


def read_password_entry(path: Path):
    """user-password.py から (ユーザー名, BotPassword名, パスワード) を取り出す。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple) and len(node.elts) >= 2:
            user_node, call_node = node.elts[0], node.elts[1]
            if (
                isinstance(user_node, ast.Constant)
                and isinstance(call_node, ast.Call)
                and getattr(call_node.func, "id", "") == "BotPassword"
                and len(call_node.args) == 2
                and all(isinstance(a, ast.Constant) for a in call_node.args)
            ):
                return user_node.value, call_node.args[0].value, call_node.args[1].value
    return None


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
        entry = read_password_entry(password_path)
        if entry is None:
            print("NG: user-password.py の形式を読み取れませんでした")
            print("    ('YourBotName', BotPassword('your-botpassword-name', '...')) の形になっているか確認してください")
            ok = False
        else:
            user, bot_name, password = entry
            print(f"user-password.py のアカウント名: {user!r}")
            print(f"  アンダースコア判定: {describe_underscore(user)}")
            print(f"BotPassword の名前: {bot_name!r}（発行した名前と一致していますか？）")
            print(f"パスワード: 長さ {len(password)} 文字 / "
                  f"半角英数字のみ: {password.isascii() and password.isalnum()}")
            if user != EXPECTED_USERNAME:
                print("  NG: アカウント名が一致しません")
                ok = False
            if password == PLACEHOLDER:
                print("  NG: パスワードがサンプルのままです。発行されたものに書き換えてください")
                ok = False
            elif password.strip() != password:
                print("  NG疑い: パスワードの前後に空白が入っています")
                ok = False

    print("=> 名前と形式は問題なし。あとはパスワードの値そのものが正しいかだけです"
          if ok else "=> 上の NG を直してから、もう一度 python -m bot.check_site を実行してください")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
