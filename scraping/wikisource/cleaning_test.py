import unittest
from bs4 import BeautifulSoup, NavigableString
import re

class HTMLCleaner:
    def clean_text(self, content: str) -> str:
        """Clean only <a> tags while preserving spacing and structure."""
        if not content:
            return ""
                
        soup = BeautifulSoup(content, 'html.parser')
        
        for a_tag in soup.find_all('a'):
            # Get text content without modifying its internal spacing
            text = a_tag.get_text()
            
            # Handle empty tags
            if not text.strip():
                text = ' ' if a_tag.string and ' ' in a_tag.string else ''
            else:
                # Check what comes after the tag
                next_sibling = a_tag.next_sibling
                next_char = None
                if isinstance(next_sibling, NavigableString):
                    if next_sibling.string:
                        next_char = next_sibling.string[0]
                        if not next_char in {'·', '.', ',', ';', ':', '!', '?', ')', ']', '}', ' ', '\n', '\t'}:
                            text += ' '
                
                # Check what comes before the tag
                prev_sibling = a_tag.previous_sibling
                if isinstance(prev_sibling, NavigableString):
                    if prev_sibling.string and not prev_sibling.string.endswith((' ', '\n', '\t')):
                        text = ' ' + text
            
            a_tag.replace_with(NavigableString(text))
        
        return str(soup)

class TestHTMLCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = HTMLCleaner()

    def test_provided_examples(self):
        """Test the specific examples provided."""
        # Example 1
        input_text = '<a class="mw-selflink-fragment" href="#p1">1</a>Ἀριστοτέλης Νικομάχου καὶ Φαιστίδος Σταγειρίτης'
        expected = '1 Ἀριστοτέλης Νικομάχου καὶ Φαιστίδος Σταγειρίτης'
        self.assertEqual(self.cleaner.clean_text(input_text), expected)

        # Example 2
        input_text = 'μετάφραση:<a href="/wiki/path">Παλατινή Ανθολογία/VII/416</a>'
        expected = 'μετάφραση: Παλατινή Ανθολογία/VII/416'
        self.assertEqual(self.cleaner.clean_text(input_text), expected)

    def test_a_tag_spacing(self):
        """Test spacing around <a> tags."""
        test_cases = [
            # Normal word following
            (
                '<a href="#">Link</a>word',
                'Link word'
            ),
            # Punctuation following
            (
                '<a href="#">Link</a>.',
                'Link.'
            ),
            # Space already exists
            (
                '<a href="#">Link</a> word',
                'Link word'
            ),
            # Multiple punctuation cases
            (
                '<a href="#">Link</a>· next',
                'Link· next'
            ),
            # No space needed after
            (
                '<a href="#">Link</a>.',
                'Link.'
            ),
            # Space needed before
            (
                'word<a href="#">Link</a>',
                'word Link'
            ),
            # Multiple tags in sequence
            (
                '<a href="#">Link1</a><a href="#">Link2</a>word',
                'Link1 Link2 word'
            ),
            # Tags with spaces between
            (
                '<a href="#">Link1</a> <a href="#">Link2</a>',
                'Link1 Link2'
            ),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.cleaner.clean_text(input_text)
                self.assertEqual(result, expected)

    def test_empty_and_whitespace_tags(self):
        """Test handling of empty or whitespace-only <a> tags."""
        test_cases = [
            ('<a></a>', ''),
            ('<a> </a>', ' '),  # Empty tag should be removed
            ('text<a> </a>next', 'text next'),  # Empty tag should be removed
            ('text <a></a> next', 'text  next'),  # Preserve original spaces
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.cleaner.clean_text(input_text)
                self.assertEqual(result, expected)

    def test_newline_handling(self):
        """Test handling of newlines in text with <a> tags."""
        test_cases = [
            # Basic newline preservation
            (
                'First line\n<a>Second</a> line\nThird line',
                'First line\nSecond line\nThird line'
            ),
            # Multiple newlines
            (
                'Line1\n\n<a>Line2</a>\n\nLine3',
                'Line1\n\nLine2\n\nLine3'
            ),
            # Mixed spaces and newlines
            (
                'Line1   \n   <a>Line2</a>   \n   Line3',
                'Line1   \n   Line2   \n   Line3'
            ),
            # Preserve spacing around punctuation
            (
                'Text<a>Link</a>.\n   New line<a>Link2</a>!',
                'Text Link.\n   New line Link2!'
            ),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.cleaner.clean_text(input_text)
                self.assertEqual(result, expected)

    def test_none_input(self):
        """Test handling of None input."""
        self.assertEqual(self.cleaner.clean_text(None), "")

if __name__ == '__main__':
    unittest.main()