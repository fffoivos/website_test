import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from itertools import groupby

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

# Define type-subtype groupings
TYPE_SUBTYPE_GROUPS = {
    'commentary': {
        'structural': {
            'appendix', 'index', 'preface'
        },
        'explanatory': {
            'epimetrum', 'explicatio', 'notes'
        }
    },
    'textpart': {
        'poetic_structure': {
            'anapests', 'antistrophe', 'ephymnion', 'epode', 'iambics', 
            'lyric', 'poem', 'proode', 'strophe', 'trochees', 'verse'
        },
        'dramatic': {
            'castlist', 'choral', 'close', 'dramatispersonae', 'episode', 'hypothesis'
        },
        'structural_divisions': {
            'book', 'centuria', 'chapter', 'folio', 'page', 'part', 'volume', 'work'
        },
        'textual_divisions': {
            'line', 'lines', 'paragraph', 'section', 'subsection', 'sentence'
        },
        'content_units': {
            'aphorism', 'comment', 'commentary', 'entry', 'epigraph', 'epistle', 
            'essay', 'excerpt', 'fable', 'fabula', 'fragment', 'haeresis', 
            'heading', 'homilia', 'letter', 'psalm', 'quaestio', 'sigla', 'source'
        }
    }
}

def analyze_div_types(root_dir):
    type_subtype_counts = defaultdict(int)
    total_files = 0

    # Process files and collect counts
    for first_level_dir in os.listdir(root_dir):
        first_level_path = os.path.join(root_dir, first_level_dir)
        if not os.path.isdir(first_level_path):
            continue
            
        for second_level_dir in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level_dir)
            if not os.path.isdir(second_level_path):
                continue
                
            for filename in os.listdir(second_level_path):
                if filename.startswith("__") or not filename.endswith(".xml"):
                    continue
                    
                file_path = os.path.join(second_level_path, filename)
                total_files += 1
                
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    for div in root.findall(".//tei:div", ns):
                        div_type = div.get('type', '')
                        subtype = div.get('subtype', '')
                        if div_type and subtype:
                            type_subtype_counts[(div_type, subtype)] += 1
                            
                except ET.ParseError:
                    print(f"Error parsing file: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")

    # Print results hierarchically
    print(f"\nType-Subtype Pairs and Counts ({total_files} files processed):")
    print("=" * 60)

    # Group by type
    sorted_items = sorted(type_subtype_counts.items(), key=lambda x: (x[0][0], x[0][1]))
    for div_type, type_group in groupby(sorted_items, key=lambda x: x[0][0]):
        print(f"\nType-Subtype Pairs and Counts ({total_files} files processed):")
        print("=" * 60)

        sorted_items = sorted(type_subtype_counts.items(), key=lambda x: (x[0][0], x[0][1]))
        for div_type, type_group in groupby(sorted_items, key=lambda x: x[0][0]):
            print(f"\n{div_type.upper()}")
            print("-" * 20)
            
            type_group_list = list(type_group)
            type_total = sum(count for (_, _), count in type_group_list)
            print(f"Total occurrences: {type_total}\n")
            
            if div_type in TYPE_SUBTYPE_GROUPS:
                for group_name, subtypes in TYPE_SUBTYPE_GROUPS[div_type].items():
                    group_items = [(st, count) for (t, st), count in type_group_list if st in subtypes]
                    if group_items:
                        print(f"  {group_name.upper()}")
                        print("  " + "-" * 18)
                        group_total = sum(count for _, count in group_items)
                        for subtype, count in sorted(group_items):
                            print(f"    {subtype:20} : {count:6}")
                        print(f"    {'TOTAL':20} : {group_total:6}\n")
                
                # Check for any ungrouped subtypes
                all_grouped = {st for groups in TYPE_SUBTYPE_GROUPS[div_type].values() for st in groups}
                ungrouped = [(st, count) for (t, st), count in type_group_list if st not in all_grouped]
                if ungrouped:
                    print("  UNGROUPED")
                    print("  " + "-" * 18)
                    for subtype, count in sorted(ungrouped):
                        print(f"    {subtype:20} : {count:6}")
            else:
                # For types without defined groups, list all subtypes
                for (_, subtype), count in sorted(type_group_list):
                    print(f"    {subtype:20} : {count:6}")

        print(f"\nTotal files processed: {total_files}")
root_directory = "/home/fivos/Desktop/First1KGreek/data"
analyze_div_types(root_directory)