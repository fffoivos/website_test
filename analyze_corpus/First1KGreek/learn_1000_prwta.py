import os
import xml.etree.ElementTree as ET
from collections import defaultdict

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

def clean_path(path):
    # Replace the path before 'data/' with './'
    return './' + path.split('/data/')[-1] if '/data/' in path else path

def create_xml_output(total_files, type_hierarchy):
    # Create root element
    root = ET.Element("divHierarchy")
    
    # Add statistics
    stats = ET.SubElement(root, "statistics")
    total_files_elem = ET.SubElement(stats, "totalFiles")
    total_files_elem.text = str(total_files)
    
    # Add types section
    types_elem = ET.SubElement(root, "types")
    
    # Add each type and its subtypes
    for div_type in sorted(type_hierarchy.keys()):
        type_elem = ET.SubElement(types_elem, "type")
        type_elem.set("name", div_type)
        subtypes_elem = ET.SubElement(type_elem, "subtypes")
        for subtype in sorted(type_hierarchy[div_type].keys()):
            subtype_elem = ET.SubElement(subtypes_elem, "subtype")
            subtype_elem.set("name", subtype)
            path_elem = ET.SubElement(subtype_elem, "path")
            path_elem.text = type_hierarchy[div_type][subtype]
    
    return root

def analyze_div_types(root_dir):
    # Dictionary to store types and their subtypes with paths
    type_hierarchy = defaultdict(lambda: defaultdict(str))
    total_files = 0
    
    for first_level_dir in os.listdir(root_dir):
        first_level_path = os.path.join(root_dir, first_level_dir)
        if not os.path.isdir(first_level_path):
            continue
            
        for second_level_dir in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level_dir)
            if not os.path.isdir(second_level_path):
                continue
                
            for filename in os.listdir(second_level_path):
                # Check if file is an XML file and contains 'grc' in the filename
                if (filename.startswith("__") or 
                    not filename.endswith(".xml") or 
                    "grc" not in filename.lower()):
                    continue
                    
                file_path = os.path.join(second_level_path, filename)
                total_files += 1
                
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    for div in root.findall(".//tei:div", ns):
                        div_type = div.get('type', '')
                        div_subtype = div.get('subtype', '')
                        if div_type and div_subtype:  # Only consider divs with both type and subtype
                            # Only store the path if we haven't seen this subtype for this type before
                            if not type_hierarchy[div_type][div_subtype]:
                                type_hierarchy[div_type][div_subtype] = clean_path(file_path)
                                
                except ET.ParseError:
                    print(f"Error parsing file: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
    
    # Create XML structure
    root_elem = create_xml_output(total_files, type_hierarchy)
    
    # Create the XML string with proper formatting
    ET.indent(root_elem, space=" ")
    xml_str = ET.tostring(root_elem, encoding='unicode')
    
    # Get the parent directory of the root_dir (one level above 'data')
    output_dir = os.path.dirname(root_dir)
    output_path = os.path.join(output_dir, 'div_hierarchy.xml')
    
    # Write to XML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_str)
    
    print(f"XML file saved to: {output_path}")
    
    # Also print to console
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print(xml_str)

# Replace this with the actual path to your root directory
root_directory = "/home/fivos/Desktop/canonical-greekLit/data"
analyze_div_types(root_directory)