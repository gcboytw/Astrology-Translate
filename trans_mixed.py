import os
import ollama
from tqdm import tqdm
from datetime import datetime
import time

# 從設定檔匯入所有需要的參數
from translation_config import (
    SOURCE_FOLDER,
    TARGET_FOLDER,
    MODEL_NAME,
    CHUNK_SIZE,
    SYSTEM_PROMPT
)

def split_text_into_chunks(text, max_size=3000):
    """
    將文本分割成小塊，優先在換行符處分割。
    """
    chunks = []
    current_chunk = []
    current_length = 0
    
    # 依單行分割
    lines = text.split('\n')
    
    for line in lines:
        # 如果單一行本身就超大，也必須放入
        if current_length + len(line) > max_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(line)
        current_length += len(line) + 1 
        
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks

def generate_draft(chunk_text, index, total, stats, is_md=False):
    """
    第一步：生成初稿 (Draft)
    """
    rules = ""
    if is_md:
        rules = "\n\nImportant rules:\n- Preserve Markdown formatting.\n- Do NOT translate code blocks.\n- Do NOT translate URLs.\n- Do NOT add explanations.\n- Only output the translated text.\n"

    prompt = f"Please translate the following Astrology text into Traditional Chinese (Part {index}/{total}). Ensure NO simplified Chinese characters are used. Translate fully and accurately{rules}:\n\n{chunk_text}"

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            system=SYSTEM_PROMPT,
            prompt=prompt,
            options={
                'temperature': 0.3, # 保持翻譯穩定
                'num_ctx': 8192,
            }
        )
        # 統計 Token
        if 'prompt_eval_count' in response:
            stats['input_tokens'] += response['prompt_eval_count']
        if 'eval_count' in response:
            stats['output_tokens'] += response['eval_count']
            
        return response['response']
    except Exception as e:
        print(f"\n[錯誤] 初稿生成失敗 {index}: {e}")
        return None

def verify_and_refine_chunk(original_text, draft_translation, stats):
    """
    第二步：自我核對與修正 (Critique & Refine)
    """
    verify_prompt = f"""
Original Text:
{original_text}

Draft Translation:
{draft_translation}

Task:
Please review the draft translation for specific errors:
1. **Mistranslated Proper Nouns**: especially "Moon Maiden" (should be "月亮少女" or "月之女", NOT "月亮處女座").
2. **Hallucinated Constellations**: Ensure "Maiden" is not translated as "Virgo" (處女座) unless it refers to the sign itself. 
3. **Common Confusion**: Ensure "Capricorn" is "磨羯座", "Aries" is "白羊座".

Action:
If the draft contains errors, output the CORRECTED translation only.
If the draft is perfect, output the original draft exactly as is.
"""
    try:
        response = ollama.generate(
            model=MODEL_NAME,
            system="You are a strict translation editor. Your job is to catch hallucinations and term errors.",
            prompt=verify_prompt,
            options={
                'temperature': 0.3, # 核對時要非常嚴謹
                'num_ctx': 8192,
            }
        )
        # 統計 Token
        if 'prompt_eval_count' in response:
            stats['input_tokens'] += response['prompt_eval_count']
        if 'eval_count' in response:
            stats['output_tokens'] += response['eval_count']

        return response['response']
    except Exception as e:
        print(f"\n[錯誤] 核對修正失敗: {e}")
        return draft_translation # 如果核對失敗，至少回傳初稿

def translate_file(file_path, output_path, stats):
    is_md = file_path.lower().endswith('.md')

    # 嘗試多種編碼讀取
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'big5', 'gbk']
    content = None
    
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"    成功使用 {enc} 編碼讀取")
            break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        print(f"[錯誤] 無法識別檔案編碼: {file_path}")
        return False

    # 切割文本
    chunks = split_text_into_chunks(content, CHUNK_SIZE)
    if not chunks:
        print(f"[警告] 檔案 {file_path} 內容似乎為空。")
        return False

    translated_parts = []
    print(f"  - 檔案較大，已分割為 {len(chunks)} 個片段進行翻譯...")

    for i, chunk in enumerate(chunks, 1):
        print(f"    [Step 1/2] 翻譯初稿中... ({i}/{len(chunks)})")
        draft = generate_draft(chunk, i, len(chunks), stats, is_md=is_md)
        
        if draft:
            print(f"    [Step 2/2] 自我核對與修正中... ({i}/{len(chunks)})")
            final_part = verify_and_refine_chunk(chunk, draft, stats)
            translated_parts.append(final_part)
        else:
            print(f"    [失敗] 片段 {i} 翻譯失敗，將保留原文佔位。")
            translated_parts.append(f"\n\n[Translation Failed for Chunk {i}]\n\n{chunk}\n\n")

    # 合併結果
    final_text = '\n\n'.join(translated_parts)
    
    # 添加 Obsidian YAML tags
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yaml_header = f"---\ncreated: {now}\ntags: [astrology]\n---\n\n"
    final_text = yaml_header + final_text
        
    # 寫入檔案
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    return True

def main():
    start_time = time.time()
    
    # 初始化統計資料
    stats = {
        'input_tokens': 0,
        'output_tokens': 0
    }

    # 建立目標資料夾
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"已建立目標資料夾: {TARGET_FOLDER}")

    # 讀取待翻譯檔案清單
    files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith('.txt') or f.endswith('.md')]
    files.sort() # 確保按章節順序處理

    print(f"找到 {len(files)} 個檔案，準備開始翻譯...")

    for file_name in tqdm(files, desc="翻譯進度"):
        source_path = os.path.join(SOURCE_FOLDER, file_name)
        if file_name.endswith('.txt'):
            target_file_name = file_name.replace('.txt', '.md')
        else:
            target_file_name = file_name
        target_path = os.path.join(TARGET_FOLDER, target_file_name)

        # 斷點續傳邏輯
        if os.path.exists(target_path):
            print(f"檔案已存在，跳過: {file_name}")
            continue

        print(f"\n正在翻譯: {file_name}")
        success = translate_file(source_path, target_path, stats)
        if not success:
            print(f"暫停處理：{file_name}")
            # 視需求決定是否中斷，這裡選擇繼續下一個
            # break 
            
    print("\n任務完成！請至 trans_ok_md 資料夾查看結果。")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("-" * 30)
    print(f"本次翻譯統計摘要：")
    print(f"總耗時: {elapsed_time:.2f} 秒")
    print(f"Input Tokens (Prompt): {stats['input_tokens']}")
    print(f"Output Tokens (Response): {stats['output_tokens']}")
    print(f"Total Tokens: {stats['input_tokens'] + stats['output_tokens']}")
    print("-" * 30)

if __name__ == "__main__":
    main()
