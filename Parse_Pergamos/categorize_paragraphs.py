import re
import os
import parse_pergamos as pct

os.makedirs('clean_output', exist_ok=True)
list_text = []
stat_outputfile = os.path.join('clean_output', 'stat_file')
with open(stat_outputfile, 'w', encoding='utf-8') as stat_file:
        stat_file.write('')
for i,file in enumerate(os.listdir('test_output')) :
    if not file.startswith('good'):
            continue
    try:
        with open('test_output'+'/'+file, 'r', encoding='utf-8') as infile:
            text = infile.read()
    except Exception as e:
        print(f"Error reading {file}: {e}")
        continue

    paragraphs = pct.paragraph_maker(text,maxpadding=1)
    #paragraphs = pct.paragraph_clean_image(paragraphs)
    paragraphs = pct.paragraph_clean_dotlines(paragraphs)
    paragraphs = pct.paragraph_remove_artifacts(paragraphs)
    paragraphs = pct.paragraph_fix_broken_line(paragraphs)
    paragraphs = pct.paragraph_merger(paragraphs,500,10)
    paragraphs = pct.remove_numbered_title(paragraphs,pct.remove_title_number_pattern)

    t_file = file

    output_file_path = os.path.join('clean_output', t_file)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            pct.test_write_text(paragraphs,output_file)
            list_text.append(pct.total_paragraphs(paragraphs))
        with open(stat_outputfile, 'a+', encoding='utf-8') as stat_file:
            pct.stat_assembly(pct.total_paragraphs(paragraphs),paragraphs)
            stat_file.write(t_file+' : '+str(pct.file_stat_list)+'\n')
        pct.file_stat_list = pct.file_reset_list()
    except Exception as e:
            print(f"Error writing to {output_file_path}: {e}")
            continue