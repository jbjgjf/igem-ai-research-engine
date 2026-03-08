import unittest
from unittest.mock import MagicMock, patch
from integrations.notion_client import NotionIntegration

class TestNotionFormatting(unittest.TestCase):
    def setUp(self):
        self.notion = NotionIntegration()

    def test_clean_text_list(self):
        input_list = ["item1", "item2"]
        expected = "- item1\n- item2"
        self.assertEqual(self.notion._clean_text(input_list), expected)

    def test_clean_text_dict(self):
        input_dict = {"a": 1, "b": [2, 3]}
        # Since _clean_text is recursive: 
        # a: 1
        # b: - 2
        # - 3
        result = self.notion._clean_text(input_dict)
        self.assertIn("a: 1", result)
        self.assertIn("b: - 2\n- 3", result)

    def test_normalize_select_bio(self):
        self.assertEqual(self.notion._normalize_select("E. coli bacteria"), "bacteria")
        self.assertEqual(self.notion._normalize_select("Human Hela cells"), "mammalian cells")
        self.assertEqual(self.notion._normalize_select("unknown"), "Unknown")

    def test_normalize_multi_select(self):
        self.assertEqual(self.notion._normalize_multi_select("a, b; c"), ["A", "B", "C"])
        self.assertEqual(self.notion._normalize_multi_select(["a", "b"]), ["A", "B"])

if __name__ == '__main__':
    unittest.main()
