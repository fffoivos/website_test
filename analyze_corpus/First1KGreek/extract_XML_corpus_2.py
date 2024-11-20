import os
import csv
from lxml import etree
from typing import Set, Optional, Tuple, List
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class XMLTextExtractor:
    def __init__(self):
        self.valid_div_types = {'textpart', 'edition'}
        self.valid_subtypes = {
            'chapter', 'paragraph', 'verse', 'fragment', 'section', 'subsection',
            'line', 'speaker', 'epistle', 'work', 'episode', 'lyric',
            'hypothesis', 'castlist', 'book', 'part', 'head',
            # New additions:
            'strophe', 'antistrophe', 'epode', 'dialogue', 'speech',
            'hexameter', 'iambic', 'trochaic', 'poem', 'monody'
        }
        self.ignore_tags = {
            'label','note', 'ref', 'bibl', 'foreign', 'figDesc', 'graphic',
            'figure', 'app', 'rdg', 'fw', 'back', 'teiHeader', 'milestone'
        }
        self.namespace = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
    def is_valid_div(self, div_elem: etree._Element) -> bool:
        """
        Check if a div element meets the criteria for text extraction.
        """
        div_type = div_elem.get('type')
        div_subtype = div_elem.get('subtype')
        
        if div_type in self.valid_div_types:
            return True
        if div_subtype in self.valid_subtypes:
            return True
        return False

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text while preserving empty lines and structure.
        """
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(line.split())
            if cleaned_line:  # Only append non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

    def process_element_text(self, element: etree._Element) -> str:
        """
        Process text directly attached to an element, excluding nested elements.
        """
        if element.tag.split('}')[-1] in self.ignore_tags:
            return ""
            
        text_parts = []
        
        # Add the element's direct text if it exists
        if element.text and element.text.strip():
            text_parts.append(element.text.strip())
            
        # Add the tail text if it exists
        if element.tail and element.tail.strip():
            text_parts.append(element.tail.strip())
            
        return ' '.join(text_parts)

    def extract_nested_text(self, div_elem: etree._Element) -> List[str]:
        """
        Recursively extract text from a div element, handling nested structure.
        Returns a list of text fragments in document order.
        """
        text_parts = []
        
        # First, get any text directly in this div before nested elements
        if div_elem.text and div_elem.text.strip():
            text_parts.append(div_elem.text.strip())
        
        # Process all child elements in order
        for child in div_elem:
            child_tag = child.tag.split('}')[-1]
            
            if child_tag == 'div':
                # If it's a div, recursively process it if valid
                if self.is_valid_div(child):
                    nested_text = self.extract_nested_text(child)
                    text_parts.extend(nested_text)
            elif child_tag not in self.ignore_tags:
                # For non-div elements that aren't ignored, process their text
                child_text = self.process_element_text(child)
                if child_text:
                    text_parts.append(child_text)
                    
                # Process their children (except for nested divs which are handled separately)
                for grandchild in child:
                    if grandchild.tag.split('}')[-1] != 'div':
                        grandchild_text = self.process_element_text(grandchild)
                        if grandchild_text:
                            text_parts.append(grandchild_text)
            
            # Get any tail text
            if child.tail and child.tail.strip():
                text_parts.append(child.tail.strip())
        
        return text_parts

    def extract_text_from_xml(self, xml_file: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract text content and metadata from XML file.
        """
        try:
            parser = etree.XMLParser(recover=True, encoding='utf-8')
            tree = etree.parse(xml_file, parser)
            root = tree.getroot()

            # Extract author
            author_elems = root.xpath('.//tei:author', namespaces=self.namespace)
            author = author_elems[0].text.strip() if author_elems else 'Unknown'

            # Extract title
            title_elems = root.xpath('.//tei:titleStmt/tei:title', namespaces=self.namespace)
            title = title_elems[0].text.strip() if title_elems else 'Unknown'

            # Get the main edition div
            edition_div = root.xpath('.//tei:text/tei:body/tei:div[@type="edition"]', namespaces=self.namespace)
            
            if not edition_div:
                logging.warning(f"No edition div found in {xml_file}")
                return author, title, ""
                
            logging.info(f"\nProcessing file: {xml_file}")
            
            # Extract text from the edition div
            text_parts = self.extract_nested_text(edition_div[0])
            
            # Join text parts with newlines
            text_content = '\n'.join(filter(None, text_parts))
            text_content = self.clean_text(text_content)

            if text_content:
                logging.info(f"Successfully extracted text (length: {len(text_content)} characters)")
            else:
                logging.warning("No text content was extracted")

            return author, title, text_content

        except Exception as e:
            logging.error(f"Error parsing {xml_file}: {str(e)}")
            return None, None, None

def process_files(input_folder: str, output_folder: str, csv_output: str):
    """
    Process all XML files in the input folder and generate output files.
    """
    extractor = XMLTextExtractor()
    data = []
    index = 1
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Calculate maximum depth to traverse
    max_depth = Path(input_folder).resolve().parts.__len__() + 2

    # Process all files
    for root_dir, sub_dirs, files in os.walk(input_folder):
        current_depth = Path(root_dir).resolve().parts.__len__()
        if current_depth > max_depth:
            del sub_dirs[:]
        
        logging.info(f"Processing directory: {root_dir}")
        
        for file_name in files:
            if not file_name.startswith('_') and 'grc' in file_name and file_name.endswith('.xml'):
                logging.info(f"Processing file: {file_name}")
                xml_file_path = os.path.join(root_dir, file_name)
                
                try:
                    author, title, text_content = extractor.extract_text_from_xml(xml_file_path)
                    
                    if text_content:
                        txt_file_name = os.path.splitext(file_name)[0] + '.txt'
                        txt_file_path = os.path.join(output_folder, txt_file_name)
                        
                        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                            txt_file.write(text_content)
                        
                        data.append({
                            'index': index,
                            'author': author,
                            'title': title,
                            'filename': file_name,
                            'original_path': xml_file_path,
                            'extracted_path': txt_file_path
                        })
                        index += 1
                        logging.info(f"Successfully processed {file_name}")
                    else:
                        logging.warning(f"No valid text content found in {file_name}")
                
                except Exception as e:
                    logging.error(f"Error processing {file_name}: {str(e)}")
            else:
                logging.debug(f"Skipping file: {file_name}")

    # Write data to CSV file
    if data:
        csv_columns = ['index', 'author', 'title', 'filename', 'original_path', 'extracted_path']
        try:
            with open(csv_output, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for entry in data:
                    writer.writerow(entry)
            logging.info(f"CSV file created at {csv_output}")
        except Exception as e:
            logging.error(f"Error writing CSV file: {str(e)}")
    else:
        logging.warning("No data to write to CSV.")

def main():
    """Main entry point of the script."""
    input_folder = '/home/fivos/Desktop/canonical-greekLit/data'
    output_folder = '/home/fivos/Desktop/canonical-greekLit/extracted_text_v1'
    csv_output = '/home/fivos/Desktop/canonical-greekLit/extracted_text_v1/canonical_metadata.csv'
    
    try:
        process_files(input_folder, output_folder, csv_output)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main()