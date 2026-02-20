import os
import json
import requests
import sys
import time
import textwrap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def format_output(text, max_width=85):
    """Format output text agar rapi dan mudah dibaca"""
    text = '\n'.join([line for line in text.split('\n') if line.strip()])
    
    formatted_lines = []
    
    for line in text.split('\n'):
        line_stripped = line.strip()
        
        if not line_stripped:
            formatted_lines.append('')
        elif line_stripped.startswith(('ЭТАП', 'PHASE', 'STAGE')):
            formatted_lines.append('\n' + '═' * 60)
            formatted_lines.append(line_stripped)
            formatted_lines.append('═' * 60)
        elif len(line_stripped) > 0 and line_stripped[0].isdigit() and '.' in line_stripped[:3]:
            formatted_lines.append('\n' + line_stripped)
        elif len(line_stripped) > max_width:
            wrapped = textwrap.fill(
                line_stripped,
                width=max_width,
                initial_indent='',
                subsequent_indent=''
            )
            formatted_lines.append(wrapped)
        else:
            formatted_lines.append(line_stripped)
    
    return '\n'.join(formatted_lines)

def call_api(prompt_content):
    """
    Call API dengan detection untuk response truncation
    
    Fitur:
    - Check finish_reason untuk detect truncation
    - Warning jika MAX_TOKENS terlalu rendah
    - Track token usage
    """
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",  
        "X-Title": "Text Adaptation Project"
    }
    
    data = {
        "model": config.MODEL,
        "messages": [
            {"role": "user", "content": prompt_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS
    }

    max_retries = 5
    retry_delay = 15

    for attempt in range(max_retries):
        try:
            response = requests.post(config.API_URL, headers=headers, json=data, timeout=60)

            # Handle rate limit (429)
            if response.status_code == 429:
                print(f"  Rate limit hit, waiting {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay *= 2  
                continue
            
            # Handle provider timeout (524)
            if response.status_code == 524:
                print(f"  Provider timeout (524), waiting {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            
            response.raise_for_status()
            full_result = response.json()

            if "choices" in full_result:
                # ============================================================
                # KEY FIX: Check finish_reason dan token usage
                # ============================================================
                choice = full_result["choices"][0]
                finish_reason = choice.get("finish_reason", "unknown")
                
                # Get token usage
                usage = full_result.get("usage", {})
                completion_tokens = usage.get("completion_tokens", 0)
                max_tokens = config.MAX_TOKENS
                
                # WARNING: Deteksi response truncation
                if finish_reason == "length":
                    print(f"  WARNING: Response TRUNCATED (finish_reason: length)")
                    print(f"      Completion tokens: {completion_tokens}/{max_tokens}")
                    print(f"      MAX_TOKENS terlalu rendah!")
                    print(f"      Recommendation: Increase MAX_TOKENS to {max_tokens + 2000}+")
                    
                    # Return error result
                    return {
                        "error": "Response truncated - MAX_TOKENS too low",
                        "finish_reason": "length",
                        "completion_tokens": completion_tokens,
                        "max_tokens": max_tokens,
                        "recommendation": f"Increase MAX_TOKENS from {max_tokens} to {max_tokens + 2000}"
                    }
                
                # Log token usage jika close to limit
                if completion_tokens >= max_tokens * 0.9:  # 90% utilization
                    print(f"  Token usage high: {completion_tokens}/{max_tokens} ({completion_tokens/max_tokens*100:.1f}%)")
                    if finish_reason == "stop":
                        print(f"      Completed successfully (but close to limit)")
                
                content = choice["message"]["content"]
                
                # Clean up <think> tag
                if "</think>" in content:
                    clean_content = content.split("</think>")[-1].strip()
                    try:
                        return json.loads(clean_content)
                    except:
                        return {"adapted_text": clean_content}
                
                return full_result

        except Exception as e:
            print(f"   Error in attempt {attempt + 1}: {str(e)[:100]}")
            if attempt == max_retries - 1:
                return {"error": f"Failed after {max_retries} attempts", "detail": str(e)}
            time.sleep(retry_delay)
    
    return {"error": "Unknown error"}

def is_already_processed(save_path, out_name):
    """Check apakah file sudah diproses dengan sukses"""
    filepath = os.path.join(save_path, out_name)
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Return True hanya jika TIDAK ada error atau truncation
        return "error" not in data
    except:
        return False

def save_formatted_output(result, output_dir, text_name, level):
    """Simpan result dalam format text yang rapi"""
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

def main():
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
    print(f"  Model: {config.MODEL}")
    print(f"  Temperature: {config.TEMPERATURE}")
    print(f"  Max Tokens: {config.MAX_TOKENS}")
    print("="*70 + "\n")

    # Iterate through prompts
    for p_file in os.listdir(prompt_dir):
        if not p_file.endswith(".txt"): 
            continue  
        
        technique = p_file.replace(".txt", "")
        save_path = os.path.join(output_base, technique)
        os.makedirs(save_path, exist_ok=True) 
        
        with open(os.path.join(prompt_dir, p_file), 'r', encoding='utf-8') as f:
            template = f.read()

        # Iterate through input texts
        for t_file in os.listdir(input_dir):
            if not t_file.endswith(".txt"): 
                continue
            
            text_name = t_file.replace('.txt', '')
            
            with open(os.path.join(input_dir, t_file), 'r', encoding='utf-8') as f:
                original_text = f.read()

            # Iterate through proficiency levels
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
                
                # Generate full prompt
                full_prompt = template.replace("{text}", original_text).replace("{target_level}", lvl)
                
                # Call API
                result = call_api(full_prompt)
                
                # Save JSON result
                json_path = os.path.join(save_path, out_name)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                
                # Save formatted text
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

    # Print summary
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

if __name__ == "__main__":
    main()