"""bot.text_replace の単体テスト（ネットワーク・Pywikibot 不要）。"""

import unittest

from bot.text_replace import apply_replace, make_preview


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
