"""接続確認（読み取りのみ）。

サイト情報とログインユーザーを表示し、1ページ取得できるか確認する。
このスクリプトは絶対に編集しない。

使い方:
    python -m bot.check_site [--lang ja] [--family wikipedia]
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Wikipedia への接続を確認する（読み取りのみ）")
    parser.add_argument("--lang", default="ja", help="言語コード（既定: ja）")
    parser.add_argument("--family", default="wikipedia", help="ファミリー（既定: wikipedia）")
    args = parser.parse_args()

    import pywikibot

    site = pywikibot.Site(args.lang, args.family)
    print(f"site: {site} (code={site.code}, family={site.family})")
    try:
        site.login()
        print(f"logged in as: {site.user()}")
    except Exception as exc:  # ログインできなくても読み取り確認は続ける
        print(f"login: 未ログイン（読み取りのみ続行します）: {exc}")

    page = pywikibot.Page(site, "メインページ")
    print(f"page exists: {page.title()} -> {page.exists()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
