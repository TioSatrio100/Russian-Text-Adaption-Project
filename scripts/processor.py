import os
import json
import time
from scripts.api_client import call_api
from scripts.file_handler import is_already_processed, save_formatted_output

def process_all():
    """Main processing logic"""
    input_dir = "../input_texts"
    prompt_dir = "../prompts"
    output_base = "../results"
    levels = ["B1", "B2"]

    os.makedirs(output_base, exist_ok=True)

    total_processed = 0
    total_skipped = 0
    total_formatted_only = 0
    total_errors = 0
    total_truncated = 0

    print("\n" + "="*70)
    print("TEXT ADAPTATION PROCESSING")
    print("="*70)
    print(f"Configuration:")
    print(f"  Model: {__import__('config').MODEL}")
    print(f"  Temperature: {__import__('config').TEMPERATURE}")
    print(f"  Max Tokens: {__import__('config').MAX_TOKENS}")
    print("="*70 + "\n")

    for p_file in os.listdir(prompt_dir):
        if not p_file.endswith(".txt"): 
            continue  
        
        technique = p_file.replace(".txt", "")
        save_path = os.path.join(output_base, technique)
        os.makedirs(save_path, exist_ok=True) 
        
        with open(os.path.join(prompt_dir, p_file), 'r', encoding='utf-8') as f:
            template = f.read()

        for t_file in os.listdir(input_dir):
            if not t_file.endswith(".txt"): 
                continue
            
            text_name = t_file.replace('.txt', '')
            
            with open(os.path.join(input_dir, t_file), 'r', encoding='utf-8') as f:
                original_text = f.read()

            for lvl in levels:
                out_name = f"{text_name}_{lvl}.json"
                
                if is_already_processed(save_path, out_name):
                    print(f"  [SKIP API] {out_name} already processed successfully")
                    
                    try:
                        with open(os.path.join(save_path, out_name), 'r', encoding='utf-8') as f:
                            result = json.load(f)
                        
                        print(f"    Formatting existing result for {lvl}...")
                        save_formatted_output(result, save_path, text_name, lvl)
                        
                        total_skipped += 1
                        total_formatted_only += 1
                        
                    except Exception as e:
                        print(f"    Error formatting existing file: {str(e)[:100]}")
                    
                    continue

                print(f"\nProcessing: {technique} | {t_file} | {lvl}")
                
                full_prompt = template.replace("{text}", original_text).replace("{target_level}", lvl)
                result = call_api(full_prompt)
                
                json_path = os.path.join(save_path, out_name)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                
                save_formatted_output(result, save_path, text_name, lvl)
                
                if "error" in result:
                    error_msg = result.get('error', 'Unknown')
                    if "truncated" in error_msg.lower():
                        print(f"    Truncation Error")
                        total_truncated += 1
                    else:
                        print(f"    Error: {error_msg[:80]}")
                    total_errors += 1
                else:
                    print(f"    Success")
                    total_processed += 1
                    
                print(f"    Waiting 10 seconds before next request...")
                time.sleep(10)

    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"Successfully processed: {total_processed}")
    print(f"Skipped (already processed): {total_skipped}")
    if total_formatted_only > 0:
        print(f"Files formatted only (no API call): {total_formatted_only}")
    if total_truncated > 0:
        print(f"TRUNCATION ERRORS: {total_truncated}")
        print(f"   Recommendation: Increase MAX_TOKENS in .env")
    print(f"Other Errors: {total_errors - total_truncated}")
    print(f"Results saved to: {output_base}")
    print("="*70 + "\n")