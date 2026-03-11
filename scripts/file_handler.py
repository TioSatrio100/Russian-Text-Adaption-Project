import os
import json
from scripts.formatter import format_output

def is_already_processed(save_path, out_name):
    filepath = os.path.join(save_path, out_name)
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return "error" not in data
    except:
        return False

def save_formatted_output(result, output_dir, text_name, level):
    if "error" in result:
        print(f"    Skipping formatted output due to error")
        return
    
    content = result.get("adapted_text", json.dumps(result, ensure_ascii=False, indent=2))
    formatted_content = format_output(content)
    
    txt_filename = f"{text_name}_{level}_formatted.txt"
    txt_path = os.path.join(output_dir, txt_filename)
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    print(f"    Formatted text saved: {txt_filename}")