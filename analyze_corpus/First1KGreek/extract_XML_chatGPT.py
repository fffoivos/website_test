import os
import xml.etree.ElementTree as ET
import pandas as pd
import re

class GreekTextProcessor:
    def __init__(self):
        self.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        self.valid_div_types = {'textpart', 'edition'}
        self.valid_subtypes = {
            'chapter', 'paragraph', 'verse', 'fragment', 'section', 'subsection',
            'line', 'speaker', 'epistle', 'work', 'episode', 'lyric',
            'hypothesis', 'castlist', 'book', 'part', 'head'
        }
        self.ignore_tags = {
            'note', 'ref', 'bibl', 'foreign', 'figDesc', 'graphic', 'figure',
            'app', 'rdg', 'fw', 'back', 'teiHeader', 'milestone'  # Added 'milestone' here
        }
        # Structural formatting rules
        self.structural_rules = {
            'lb': '\n',                # Line break
            'pb': '\n\n',              # Page break
            'cb': '\n\n',              # Column break
            'space': ' ',              # Space
            'p': '\n\n{}\n\n',         # Paragraph
            'l': '{}\n',               # Line of verse
            'lg': '\n{}\n',            # Line group
            'ab': '\n\n{}\n\n',        # Anonymous block
            'div': '\n\n{}\n\n',       # Division
            'head': '\n\n{}\n\n',      # Header
            'title': '\n{}\n\n',       # Title
        }
        self.content_rules = {
            'speaker': '\n{}\n',       # Speaker
            'sp': '\n{}\n',            # Speech
            'quote': '"{}"',           # Quotation
            'q': '"{}"',               # Quoted text
            'gap': '[...]',            # Gap in text
            'unclear': '[?]',          # Unclear text
            'item': '\n{}',            # List item
            'list': '\n{}\n',          # List
            'cit': '"{}"',             # Citation
            'seg': '{} ',              # Segment
            'w': '{} ',                # Word
            'num': '{}',               # Number
            'hi': '{}',                # Highlighted text
            'emph': '{}',              # Emphasized text
            'add': '{}',               # Additions
            'del': '',                 # Deletions (content not included)
            'choice': '{}',            # Variants
            'corr': '{}',              # Corrections
            'sic': '{}',               # Errors in source text
            'orig': '{}',              # Original reading
            'reg': '{}',               # Regularization
        }

    def get_element_text(self, elem, default=''):
        """Safely extract text from an element."""
        return elem.text if (elem is not None and elem.text is not None) else default

    def normalize_whitespace(self, text):
        """Normalize whitespace in the text."""
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove trailing spaces on lines
        text = re.sub(r'[ \t]+\n', '\n', text)
        # Replace multiple blank lines with two newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def process_file(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract title and author using the helper method
        title = root.find('.//tei:titleStmt/tei:title', self.ns)
        author = root.find('.//tei:titleStmt/tei:author', self.ns)
        title_text = self.get_element_text(title, default='Unknown Title')
        author_text = self.get_element_text(author, default='Unknown Author')

        # Process text body
        body = root.find('.//tei:text/tei:body', self.ns)
        text = self.process_element(body) if body is not None else ''

        return title_text, author_text, text

    def process_element(self, elem):
        if elem is None or elem.tag is None:
            return ''
        tag = elem.tag.split('}')[-1]  # Remove namespace
        if tag in self.ignore_tags:
            if tag == 'milestone':
                # Ignore tail text for milestone to prevent line breaks
                text_content = ''
                for child in elem:
                    text_content += self.process_element(child)
                return text_content
            else:
                # For other ignored elements, process children and include tail text
                text_content = ''
                for child in elem:
                    text_content += self.process_element(child)
                tail = elem.tail if elem.tail else ''
                return text_content + tail
        elif tag in self.structural_rules:
            # Include element's own text
            text_content = elem.text if elem.text else ''
            # Process children
            content = text_content + ''.join(self.process_element(child) for child in elem)
            # Apply structural formatting
            formatted_content = self.structural_rules[tag].format(content)
            # Include tail text
            tail = elem.tail if elem.tail else ''
            return formatted_content + tail
        elif tag in self.content_rules:
            # Include element's own text
            text_content = elem.text if elem.text else ''
            # Process children
            content = text_content + ''.join(self.process_element(child) for child in elem)
            # Apply content formatting
            formatted_content = self.content_rules[tag].format(content)
            # Include tail text
            tail = elem.tail if elem.tail else ''
            return formatted_content + tail
        else:
            # Default processing for unhandled tags
            text_content = elem.text if elem.text else ''
            for child in elem:
                text_content += self.process_element(child)
            tail = elem.tail if elem.tail else ''
            return text_content + tail

    def process_files_in_directory(self, data_folder, output_folder):
        metadata = []
        index = 1
        file_count = 0  # To count the number of files processed

        for root_dir, dirs, files in os.walk(data_folder):
            # Skip directories starting with '_'
            dirs[:] = [d for d in dirs if not d.startswith('_')]
            for file_name in files:
                if file_name.endswith('.xml') and 'grc' in file_name:
                    file_path = os.path.join(root_dir, file_name)
                    try:
                        title, author, text = self.process_file(file_path)
                        # Normalize whitespace in the text
                        text = self.normalize_whitespace(text)
                        # Write text to output file
                        output_file = os.path.join(output_folder, os.path.splitext(file_name)[0] + '.txt')
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                        # Collect metadata
                        metadata.append({
                            'index': index,
                            'author': author,
                            'title': title,
                            'filename': file_name
                        })
                        index += 1
                        file_count += 1  # Increment the file count
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")

        # Write metadata to CSV
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_csv(os.path.join(output_folder, 'book_metadata.csv'), index=False)
        print(f"Processed {file_count} files.")

# Usage example
if __name__ == '__main__':
    data_folder = '/home/fivos/Desktop/First1KGreek_fork/data'  # Replace with your data folder path
    output_folder = '/home/fivos/Desktop/First1KGreek_fork/extracted_text_v3'  # Replace with your output folder path
    os.makedirs(output_folder, exist_ok=True)
    processor = GreekTextProcessor()
    processor.process_files_in_directory(data_folder, output_folder)
