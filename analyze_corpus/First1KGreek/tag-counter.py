import os
import xml.etree.ElementTree as ET
from collections import defaultdict

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

def count_tags_in_divs(root_dir):
    tag_counts = defaultdict(int)
    total_files = 0
    files_with_divs = 0
    greek_files = 0

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
                if filename.startswith("__") or not filename.endswith(".xml") or 'grc' not in filename:
                    continue

                file_path = os.path.join(second_level_path, filename)
                total_files += 1
                greek_files += 1  # Count files with 'grc' in filename
                
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    # Find the body element
                    body = root.find(".//tei:body", ns)
                    if body is not None:
                        # Find all div elements within body
                        divs = body.findall(".//tei:div", ns)
                        if divs:
                            files_with_divs += 1
                            # Count all tags within each div
                            for div in divs:
                                for elem in div.iter():
                                    # Remove namespace from tag name
                                    tag_name = elem.tag
                                    if '}' in tag_name:
                                        tag_name = tag_name.split('}')[1]
                                    if tag_name != 'div':  # Don't count the div tags themselves
                                        tag_counts[tag_name] += 1

                except ET.ParseError:
                    print(f"Error parsing file: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")

    # Create output directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'tag_counts_greek.xml')

    # Create XML output
    root = ET.Element("tagCounts")
    
    # Add statistics
    stats = ET.SubElement(root, "statistics")
    greek_files_elem = ET.SubElement(stats, "totalGreekFiles")
    greek_files_elem.text = str(greek_files)
    files_with_divs_elem = ET.SubElement(stats, "filesWithDivs")
    files_with_divs_elem.text = str(files_with_divs)
    
    # Add tag counts
    counts = ET.SubElement(root, "tags")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        tag_elem = ET.SubElement(counts, "tag")
        tag_elem.set("name", tag)
        tag_elem.set("count", str(count))

    # Write to XML file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    
    with open(output_path, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding='utf-8')

    # Print results to console
    print(f"\nTotal Greek XML files processed (with 'grc' in filename): {greek_files}")
    print(f"Files containing div elements: {files_with_divs}")
    print("\nTag counts within <div> elements:")
    print("=================================")
    
    # Sort tags by count in descending order
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags:
        print(f"<{tag}> : {count}")
        
    print(f"\nResults have been saved to: {output_path}")

# Replace this with the actual path to your root directory
root_directory = "/home/fivos/Desktop/First1KGreek/data"
count_tags_in_divs(root_directory)