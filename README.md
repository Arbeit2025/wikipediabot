# wikipediabot

日本語版 Wikipedia 向けの、Pywikibot を使った編集 Bot のスターターキットです。

- 運用 Bot アカウント：`YourBotName`（"＿" は全角 U+FF3F。半角 `_` の同名アカウントは存在しません）
- 操作者：運用者
- 状態（2026-10-29 確認）：アカウント作成済み（2026-02-23）、利用者ページ作成済み、**Bot フラグは未付与（未承認）**

**まだ承認済み Bot ではありません。** いきなり本番記事を大量編集するためのものではなく、

1. 読み取りだけで接続を確認する
2. 置換内容を dry-run（差分プレビュー）で確かめる
3. 日本語版 Wikipedia の Bot 使用申請と仮運用を経る

という順序で安全に始めるための土台です。

## 安全設計（最初から入っているもの）

- **dry-run が既定**：`--write` を付けない限り、Wikipedia へは一切書き込みません
- **未承認時の上限をコードで強制**：編集間隔 60 秒未満、1タスク 200 件超はエラーで止まります（日本語版の方針に合わせた値）
- **承認済みモードでも下限を強制**：`--approved` 時でも編集間隔 5 秒未満はエラー
- **書き込みには確認入力が必須**：`--write` のときは実行時に `WRITE` と入力しないと保存しません
- **認証情報を Git に入れない**：`user-config.py` と `user-password.py` は `.gitignore` 済み。リポジトリには `*.example` だけ置きます

詳しくは [docs/safety.md](docs/safety.md)、承認の流れは [docs/bot-approval-ja.md](docs/bot-approval-ja.md) を見てください。

## セットアップ

前提：Python 3.9 以上（開発時は 3.12 で確認）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows（コマンドプロンプト）の場合はこちら。`source` や `cp` は cmd では使えません。

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

#### Windows + Python 3.14 で mwparserfromhell のビルドに失敗する場合

`Microsoft Visual C++ 14.0 or greater is required` と出るときは、C 拡張なし（純 Python 版）で入れるのが一番簡単です。機能は同じで、解析が少し遅くなるだけです（Build Tools を入れる必要はありません）。

```bat
set WITH_EXTENSION=0
pip install -r requirements.txt
```

あるいは Python 3.12 / 3.13 を使うと、ビルド済み wheel がそのまま入ります。

### Bot アカウントと認証（BotPasswords）

1. Wikipedia で **Bot 専用アカウント**を作成する（普段使いのアカウントとは分ける）
2. そのアカウントでログインし、`特別:Botパスワード`（Special:BotPasswords）で Bot パスワードを発行する（必要な権限だけ付ける）
3. 設定ファイルを用意する

```bash
cp user-config.py.example user-config.py
cp user-password.py.example user-password.py
# 2つのファイルの中の Bot アカウント名などを自分のものに書き換える
```

Windows（cmd）では `cp` の代わりに `copy` を使います。

```bat
copy user-config.py.example user-config.py
copy user-password.py.example user-password.py
```

`user-password.py` の中身はパスワードそのものです。絶対にコミットしないでください。

## 使い方

### 1. 接続確認（読み取りのみ・編集しません）

```bash
python -m bot.check_site
```

サイト情報とログインユーザー名を表示し、メインページが取得できるかだけ確認します。

### 2. 文字列置換を dry-run で見る（書き込みません）

対象ページ名を1行1件で書いたファイル（例：`pages.txt`）を用意して、

```bash
python -m bot.run_replace --old "旧表記" --new "新表記" --pages-file pages.txt
```

各ページについて「置換が何件起きるか」と差分を表示するだけです。

### 3. 実際に書く（承認と仮運用の範囲でのみ）

```bash
python -m bot.run_replace --old "旧表記" --new "新表記" --pages-file pages.txt \
  --summary "Bot: 表記の統一" --write
```

- 編集要約（`--summary`）は書き込み時に必須です
- 実行途中で `WRITE` と入力したときだけ保存が始まります
- 承認済み Bot として動かすときだけ `--approved` を付けます（間隔の下限が 5 秒になります）

## 構成

```
bot/
  check_site.py     読み取り専用の接続確認
  text_replace.py   置換と差分生成（ネットワークなし、テスト対象）
  run_replace.py    置換 Bot 本体（dry-run 既定）
tests/
  test_text_replace.py
docs/
  bot-approval-ja.md  日本語版 Wikipedia の Bot 承認の流れ
  safety.md           安全設計と運用ルール
user-config.py.example / user-password.py.example
```

## テスト

ネットワークも Pywikibot も使わない単体テストです。

```bash
python -m unittest discover -s tests -v
```

## ライセンス

MIT License（[LICENSE](LICENSE)）
