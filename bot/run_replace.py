"""文字列置換 Bot 本体。

安全設計:
- 既定は dry-run。--write を付けない限り保存しない。
- --write のときも、実行時に WRITE と入力しない限り保存しない。
- 未承認モードでは編集間隔 60 秒未満・上限 200 件超をエラーにする
  （日本語版 Wikipedia の未承認 Bot に対する方針に合わせた値）。
- 承認済みモード (--approved) でも編集間隔 5 秒未満はエラーにする。

使い方（dry-run）:
    python -m bot.run_replace --old "旧表記" --new "新表記" --pages-file pages.txt

使い方（書き込み。承認・仮運用の範囲でのみ）:
    python -m bot.run_replace --old "旧表記" --new "新表記" --pages-file pages.txt \
        --summary "Bot: 表記の統一" --write
"""

from __future__ import annotations

import argparse
import sys
import time

from bot.text_replace import apply_replace, make_preview, replace_link_target

# 日本語版 Wikipedia の方針に合わせた下限・上限（docs/bot-approval-ja.md 参照）
UNAPPROVED_MIN_INTERVAL_SEC = 60
UNAPPROVED_MAX_EDITS = 200
APPROVED_MIN_INTERVAL_SEC = 5


def load_titles(args: argparse.Namespace) -> list[str]:
    titles: list[str] = list(args.page or [])
    if args.pages_file:
        with open(args.pages_file, encoding="utf-8") as f:
            titles.extend(line.strip() for line in f if line.strip())
    # 重複を除き、順序は保つ
    return list(dict.fromkeys(titles))


def validate_args(args: argparse.Namespace, titles: list[str]) -> None:
    if not titles:
        raise SystemExit("対象ページがありません（--page か --pages-file を指定してください）")
    if args.old == "":
        raise SystemExit("--old が空です")
    if args.old == args.new:
        raise SystemExit("--old と --new が同じです")
    min_interval = APPROVED_MIN_INTERVAL_SEC if args.approved else UNAPPROVED_MIN_INTERVAL_SEC
    if args.interval < min_interval:
        raise SystemExit(
            f"編集間隔が短すぎます: {args.interval}秒 < 下限 {min_interval}秒"
            f"（{'承認済み' if args.approved else '未承認'}モード）"
        )
    if len(titles) > args.limit:
        raise SystemExit(f"対象 {len(titles)} 件が --limit {args.limit} 件を超えています")
    if not args.approved and args.limit > UNAPPROVED_MAX_EDITS:
        raise SystemExit(
            f"未承認モードの上限は {UNAPPROVED_MAX_EDITS} 件です（--limit {args.limit}）"
        )
    if args.write and not args.summary:
        raise SystemExit("書き込みには編集要約 --summary が必須です")


def main() -> int:
    parser = argparse.ArgumentParser(description="Wikipedia の文字列置換 Bot（既定は dry-run）")
    parser.add_argument("--old", required=True, help="置換前の文字列")
    parser.add_argument("--new", required=True, help="置換後の文字列")
    parser.add_argument("--page", action="append", help="対象ページ名（複数指定可）")
    parser.add_argument("--pages-file", help="対象ページ名を1行1件で書いたファイル")
    parser.add_argument("--summary", default="", help="編集要約（--write 時は必須）")
    parser.add_argument("--lang", default="ja", help="言語コード（既定: ja）")
    parser.add_argument("--family", default="wikipedia", help="ファミリー（既定: wikipedia）")
    parser.add_argument("--limit", type=int, default=20, help="対象件数の上限（既定: 20）")
    parser.add_argument(
        "--interval", type=float, default=60.0,
        help="編集間隔（秒、既定: 60）。承認済みモードでは 5 秒以上",
    )
    parser.add_argument("--link", action="store_true",
                        help="リンク先だけを置換する（種別C: [[旧名]]→[[新名]] のリンク修正用）")
    parser.add_argument("--approved", action="store_true",
                        help="Bot フラグ承認済みアカウントで動かす場合のみ付ける")
    parser.add_argument("--write", action="store_true",
                        help="実際に保存する（付けなければ dry-run）")
    args = parser.parse_args()

    titles = load_titles(args)
    validate_args(args, titles)

    import pywikibot

    site = pywikibot.Site(args.lang, args.family)
    if args.write:
        site.login()
        print(f"ログイン中: {site.user()} / 対象 {len(titles)} 件 / 間隔 {args.interval} 秒")
        answer = input("本当に書き込みますか？ 続ける場合は WRITE と入力してください: ")
        if answer != "WRITE":
            print("中止しました（何も保存していません）")
            return 1
    else:
        print(f"[DRY-RUN] 保存はしません / 対象 {len(titles)} 件")

    saved = 0
    skipped = 0
    for idx, title in enumerate(titles):
        page = pywikibot.Page(site, title)
        if not page.exists():
            print(f"- {title}: ページが存在しないためスキップ")
            skipped += 1
            continue
        before = page.text
        if args.link:
            after, count = replace_link_target(before, args.old, args.new)
        else:
            after, count = apply_replace(before, args.old, args.new)
        if count == 0:
            print(f"- {title}: 置換対象なし")
            skipped += 1
            continue
        print(f"- {title}: {count} 件置換")
        print(make_preview(title, before, after))
        if not args.write:
            continue
        page.text = after
        # Pywikibot 11.x: Bot フラグ指定は bot 引数（botflag は非推奨の旧名）
        page.save(
            summary=args.summary,
            bot=args.approved,
            minor=False,
        )
        saved += 1
        if idx < len(titles) - 1:
            time.sleep(args.interval)

    print(f"完了: 保存 {saved} 件 / スキップ {skipped} 件 / 全 {len(titles)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
