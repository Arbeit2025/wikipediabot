"""bot.text_replace の単体テスト（ネットワーク・Pywikibot 不要）。"""

import unittest

from bot.text_replace import apply_replace, make_preview, replace_link_target


class TestApplyReplace(unittest.TestCase):
    def test_replaces_all_occurrences(self):
        after, count = apply_replace("猫と猫と犬", "猫", "ねこ")
        self.assertEqual(after, "ねことねこと犬")
        self.assertEqual(count, 2)

    def test_no_match_returns_original_and_zero(self):
        after, count = apply_replace("犬だけ", "猫", "ねこ")
        self.assertEqual(after, "犬だけ")
        self.assertEqual(count, 0)

    def test_empty_old_raises(self):
        with self.assertRaises(ValueError):
            apply_replace("文字列", "", "x")

    def test_replace_with_empty_string_deletes(self):
        after, count = apply_replace("aXbXc", "X", "")
        self.assertEqual(after, "abc")
        self.assertEqual(count, 2)


class TestReplaceLinkTarget(unittest.TestCase):
    def test_plain_link(self):
        after, count = replace_link_target("[[旧名]]へのリンク", "旧名", "新名")
        self.assertEqual(after, "[[新名]]へのリンク")
        self.assertEqual(count, 1)

    def test_piped_link_keeps_display_text(self):
        after, count = replace_link_target("[[旧名|表示名]]", "旧名", "新名")
        self.assertEqual(after, "[[新名|表示名]]")
        self.assertEqual(count, 1)

    def test_section_link_keeps_section(self):
        after, count = replace_link_target("[[旧名#歴史]]と[[旧名#歴史|あの節]]", "旧名", "新名")
        self.assertEqual(after, "[[新名#歴史]]と[[新名#歴史|あの節]]")
        self.assertEqual(count, 2)

    def test_plain_text_is_not_replaced(self):
        after, count = replace_link_target("本文中の旧名という文字列", "旧名", "新名")
        self.assertEqual(after, "本文中の旧名という文字列")
        self.assertEqual(count, 0)

    def test_similar_page_names_are_not_replaced(self):
        after, count = replace_link_target("[[旧名2]]と[[新・旧名]]", "旧名", "新名")
        self.assertEqual(after, "[[旧名2]]と[[新・旧名]]")
        self.assertEqual(count, 0)


class TestMakePreview(unittest.TestCase):
    def test_preview_contains_diff_markers(self):
        preview = make_preview("テストページ", "一行目\n猫です", "一行目\nねこです")
        self.assertIn("-猫です", preview)
        self.assertIn("+ねこです", preview)
        self.assertIn("テストページ", preview)

    def test_preview_truncates_long_diff(self):
        before = "\n".join(f"行{i} 猫" for i in range(200))
        after = "\n".join(f"行{i} ねこ" for i in range(200))
        preview = make_preview("長いページ", before, after, max_lines=10)
        self.assertIn("省略", preview)


if __name__ == "__main__":
    unittest.main()
