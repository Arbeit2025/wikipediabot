"""user-password.py を標準形式に変換する（パスワードは表示しない）。

昔の形式:
    ('ログイン名@BotPassword名', 'パスワード文字列')
という2つの文字列のタプルで書かれているファイルを、

標準形式:
    ('Botアカウント名', BotPassword('BotPassword名', 'パスワード文字列'))
に書き直す。アカウント名は user-config.py に書かれたものをそのまま使う。
パスワードの値は読み取ってそのまま移すだけで、画面にもログにも出さない。

使い方:
    python -m bot.fix_password_file [--botname 名前]

- 変換元はカレントフォルダの user-password.py（旧ファイルのコピーで上書き済みの想定）
- BotPassword 名は旧ファイルのログイン名の '@' の後ろから取り出す
- 名前を変えたい場合だけ --botname を付ける
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def read_config_username(path: Path) -> str | None:
    """user-config.py の usernames[...] = '...' からアカウント名を取り出す。"""
    if not path.exists():
        return None
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


def extract(path: Path) -> tuple[str, str]:
    """ファイルから (BotPassword名, パスワード) を取り出す。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))

    # すでに標準形式なら、そのまま取り出す
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fname == "BotPassword" and len(node.args) == 2 and all(
                isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args
            ):
                return node.args[0].value, node.args[1].value

    # 昔の形式: ('ログイン名@BotPassword名', 'パスワード')
    strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    login_names = [s for s in strings if "@" in s]
    passwords = [s for s in strings if "@" not in s and len(s) >= 8]
    if login_names and passwords:
        bot_name = login_names[0].rsplit("@", 1)[1]
        return bot_name, passwords[0]

    raise ValueError("どちらの形式でも読み取れませんでした")


def main() -> int:
    parser = argparse.ArgumentParser(description="user-password.py を標準形式に変換する")
    parser.add_argument("--botname", default="", help="BotPassword 名を上書きする場合に指定")
    parser.add_argument("--file", default="user-password.py", help="対象ファイル（既定: user-password.py）")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"NG: {path} がありません")
        return 1
    username = read_config_username(Path("user-config.py"))
    if username is None:
        print("NG: user-config.py からアカウント名を読み取れませんでした（先に user-config.py を用意してください）")
        return 1
    try:
        bot_name, password = extract(path)
    except ValueError as exc:
        print(f"NG: {exc}")
        return 1
    if args.botname:
        bot_name = args.botname

    new_content = (
        "# BotPasswords（自動変換済み。このファイルは Git に入れないこと）\n"
        f"({username!r}, BotPassword({bot_name!r}, {password!r}))\n"
    )
    path.write_text(new_content, encoding="utf-8")
    print("変換しました（パスワードは表示していません）")
    print(f"  アカウント名: {username!r}")
    print(f"  BotPassword 名: {bot_name!r}")
    print(f"  パスワード: {len(password)} 文字")
    print("次に python -m bot.check_password_file と python -m bot.check_site を実行してください")
    return 0


if __name__ == "__main__":
    sys.exit(main())
