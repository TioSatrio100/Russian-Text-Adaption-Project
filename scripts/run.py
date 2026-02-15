import os
import json
import requests
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def call_api(prompt_content):
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
        "temperature": config.TEMPERATURE
    }

    max_retries = 5
    retry_delay = 15

    for attempt in range(max_retries):
        try:
            response = requests.post(config.API_URL, headers=headers, json=data)

            # Avoid rate limit
            if response.status_code == 429:
                print(f"  Wait for limit {retry_delay} seconds (test {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay *= 2  
                continue
            
            response.raise_for_status()
            full_result = response.json()

            if "choices" in full_result:
                content = full_result["choices"][0]["message"]["content"]
                if "</think>" in content:
                    clean_content = content.split("</think>")[-1].strip()
                    try:
                        return json.loads(clean_content)
                    except:
                        return {"adapted_text": clean_content}
            return full_result

        except Exception as e:
            print(f"   Eror in test {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {"error": f"Fail after {max_retries} test", "detail": str(e)}
            time.sleep(retry_delay)
    
    return {"error": "Unknown error"}

def main():
    input_dir = "../input_texts"
    prompt_dir = "../prompts"
    output_base = "../results"
    levels = ["B1", "B2"]

    os.makedirs(output_base, exist_ok=True)

    # Take Prompts
    for p_file in os.listdir(prompt_dir):
        if not p_file.endswith(".txt"): continue  
        technique = p_file.replace(".txt", "")
        save_path = os.path.join(output_base, technique)
        os.makedirs(save_path, exist_ok=True) 
        with open(os.path.join(prompt_dir, p_file), 'r', encoding='utf-8') as f:
            template = f.read()

        # Take inputs
        for t_file in os.listdir(input_dir):
            if not t_file.endswith(".txt"): continue
            with open(os.path.join(input_dir, t_file), 'r', encoding='utf-8') as f:
                original_text = f.read()

            # Processing 
            for lvl in levels:
                print(f"Processing: {technique} | {t_file} | {lvl}")
                full_prompt = template.replace("{text}", original_text).replace("{target_level}", lvl)  
                result = call_api(full_prompt)
                out_name = f"{t_file.replace('.txt', '')}_{lvl}.json"
                with open(os.path.join(save_path, out_name), 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"    Delay 5 Seconds")
                time.sleep(5)

    print("\n[V] All task can be found in folder 'results'.")

if __name__ == "__main__":
    main()