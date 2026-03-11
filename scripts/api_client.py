import json
import time
import requests
import sys
import os

# Tambahkan parent directory ke path untuk import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def call_api(prompt_content):
    """
    Call API dengan detection untuk response truncation
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

            if response.status_code == 429:
                print(f"  Rate limit hit, waiting {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay *= 2  
                continue
            
            if response.status_code == 524:
                print(f"  Provider timeout (524), waiting {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            
            response.raise_for_status()
            full_result = response.json()

            if "choices" in full_result:
                choice = full_result["choices"][0]
                finish_reason = choice.get("finish_reason", "unknown")
                
                usage = full_result.get("usage", {})
                completion_tokens = usage.get("completion_tokens", 0)
                max_tokens = config.MAX_TOKENS
                
                if finish_reason == "length":
                    print(f"  WARNING: Response TRUNCATED (finish_reason: length)")
                    print(f"      Completion tokens: {completion_tokens}/{max_tokens}")
                    print(f"      MAX_TOKENS terlalu rendah!")
                    print(f"      Recommendation: Increase MAX_TOKENS to {max_tokens + 2000}+")
                    
                    return {
                        "error": "Response truncated - MAX_TOKENS too low",
                        "finish_reason": "length",
                        "completion_tokens": completion_tokens,
                        "max_tokens": max_tokens,
                        "recommendation": f"Increase MAX_TOKENS from {max_tokens} to {max_tokens + 2000}"
                    }
                
                if completion_tokens >= max_tokens * 0.9:
                    print(f"  Token usage high: {completion_tokens}/{max_tokens} ({completion_tokens/max_tokens*100:.1f}%)")
                    if finish_reason == "stop":
                        print(f"      Completed successfully (but close to limit)")
                
                content = choice["message"]["content"]
                
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