import xml.etree.ElementTree as ET

def extract_fragments(input_file_path, output_path):
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    try:
        tree = ET.parse(input_file_path)
        root = tree.getroot()
        text_elem = root.find('.//tei:text', ns)
        
        if text_elem is None:
            print("No text element found")
            return

        formatted_text = []
        current_line = []
        
        def process_element(elem):
            nonlocal current_line, formatted_text
            
            tag = elem.tag.split('}')[-1]
            
            # Handle fragments and their contents
            if tag == 'div' and elem.get('subtype') == 'fragment':
                if current_line:
                    formatted_text.append(' '.join(current_line))
                    current_line = []
                formatted_text.append('\n\n')  # Space between fragments
            
            elif tag == 'p':
                if current_line:
                    formatted_text.append(' '.join(current_line))
                    current_line = []
                formatted_text.append('\n')
            
            elif tag == 'lb':
                if current_line:
                    formatted_text.append(' '.join(current_line))
                    current_line = []
                formatted_text.append('\n')
            
            # Handle the element's text content
            if elem.text and elem.text.strip():
                current_line.append(elem.text.strip())
            
            # Process all child elements
            for child in elem:
                process_element(child)
                
                # Handle any tail text after the child
                if child.tail and child.tail.strip():
                    current_line.append(child.tail.strip())
        
        # Process the entire text element
        process_element(text_elem)
        
        # Flush any remaining text
        if current_line:
            formatted_text.append(' '.join(current_line))
        
        # Clean up: normalize multiple newlines
        clean_text = ''.join(formatted_text)
        while '\n\n\n' in clean_text:
            clean_text = clean_text.replace('\n\n\n', '\n\n')
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(clean_text.strip())
        
        print(f"Successfully created text file: {output_path}")
        
    except ET.ParseError:
        print(f"Error parsing file: {input_file_path}")
    except Exception as e:
        print(f"Error processing file {input_file_path}: {str(e)}")

# Process the specific file
input_file = "/home/fivos/Desktop/text_sources/OpenGreekAndLatin-First1KGreek-de360a3/data/tlg1664/tlg001/tlg1664.tlg001.1st1K-grc1.xml"
output_file = "fragments.txt"

extract_fragments(input_file, output_file)