import os
import ollama
from tqdm import tqdm
import time

# --- 設定區 ---
SOURCE_FOLDER = 'regular_trans'
TARGET_FOLDER = 'regular_trans_ok'
MODEL_NAME = 'translategemma:12b'
CHUNK_SIZE = 3000  # 每次處理的字元數限制，確保不超過 Context Window

# 系統指令：一般文件與日常對話的翻譯規則
SYSTEM_PROMPT = """
Role: 你是一位精通繁體中文的專業翻譯助理。
Target Language: 繁體中文 (Traditional Chinese, Taiwan Standard)
Background & Style:
- 任務：將英文內容翻譯為繁體中文。文件來源通常是 GitHub 上的開源說明文件 (README 等)，或是日常生活對話的英翻中。
- 語氣：口吻語氣貼近生活用法即可，自然流暢、口語化，不需要過於嚴肅或專業死板。
- 規則：
1. **譯名標準**：優先使用台灣常見的科技名詞、開發者習慣用語或日常慣用語。
2. **語序優化**：請根據中文習慣調整語序，避免英文式的倒裝句法，讓句子通順自然。
3. **格式保持**：請務必完整保留原文的 Markdown 排版符號、程式碼區塊 (Code blocks)、連結 (Links)、表格與段落結構。這非常重要。
4. **內容完整**：精準還原原意，嚴禁摘要、刪減或擅自添加內容。
5. **拒絕機器感**：減少「被...」等被動語態，減少不必要的「的」字，讓語句更為乾淨利落。
Mandatory: 請確保輸出內容完全為繁體中文，且讀起來自然流暢。
"""

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

def translate_chunk(chunk_text, index, total, is_md=False):
    """
    翻譯單一文本塊
    """
    rules = ""
    if is_md:
        rules = "\n\nImportant rules:\n- Preserve Markdown formatting.\n- Do NOT translate code blocks.\n- Do NOT translate URLs.\n- Do NOT add explanations.\n- Only output the translated text.\n"

    prompt = f"Please translate the following text into Traditional Chinese (Part {index}/{total}). Ensure NO simplified Chinese characters are used. Translate fully and accurately, preserving all original markdown formatting:{rules}\n\n{chunk_text}"

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            system=SYSTEM_PROMPT,
            prompt=prompt,
            options={
                'temperature': 0.3, # 保持翻譯穩定
                'num_ctx': 8192,    # 確保足夠的上下文視窗
                'top_p': 0.9,      # 增加一點用詞的豐富度
                'top_k': 40,        # 限制模型從前 40 個最可能的字中選擇，增加用語精準度。
                'repeat_penalty': 1.1, # 稍微增加處罰，防止長文翻譯中出現重複句式。
            }
        )
        return response['response']
    except Exception as e:
        print(f"\n[錯誤] 翻譯片段 {index} 時發生問題: {e}")
        return None

def translate_file(file_path, output_path):
    is_md = file_path.lower().endswith('.md')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 切割文本
    chunks = split_text_into_chunks(content, CHUNK_SIZE)
    if not chunks:
        print(f"[警告] 檔案 {file_path} 內容似乎為空。")
        # 建立空檔案以保持結構一致
        with open(output_path, 'w', encoding='utf-8') as f:
            pass
        return True

    translated_parts = []
    if len(chunks) > 1:
        print(f"  - 檔案較大，已分割為 {len(chunks)} 個片段進行翻譯...")

    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            print(f"    轉換中... ({i}/{len(chunks)})")
        translated_part = translate_chunk(chunk, i, len(chunks), is_md=is_md)
        
        if translated_part:
            translated_parts.append(translated_part)
        else:
            print(f"    [失敗] 片段 {i} 翻譯失敗，將保留原文佔位。")
            translated_parts.append(f"\n\n[Translation Failed for Chunk {i}]\n\n{chunk}\n\n")

    # 合併結果，由於可能有多個 chunk，保持合適的間距
    final_text = '\n\n'.join(translated_parts) if len(chunks) > 1 else translated_parts[0]
    
    # 寫入檔案
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    return True

def main():
    start_time = time.time()

    # 建立目標與來源資料夾
    if not os.path.exists(SOURCE_FOLDER):
        os.makedirs(SOURCE_FOLDER)
        print(f"提示: 已建立來源資料夾: {SOURCE_FOLDER}，請將要翻譯的檔案放入此處。")
        return
        
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"已建立目標資料夾: {TARGET_FOLDER}")

    # 讀取待翻譯檔案清單 (保留目錄結構，包括 .txt 和 .md)
    files_to_process = []
    for root, _, files in os.walk(SOURCE_FOLDER):
        for file in files:
            if file.lower().endswith(('.txt', '.md')):
                # 取得相對路徑
                rel_path = os.path.relpath(os.path.join(root, file), SOURCE_FOLDER)
                files_to_process.append(rel_path)
                
    files_to_process.sort()

    if not files_to_process:
        print(f"在 {SOURCE_FOLDER} 中沒有找到任何 .txt 或 .md 檔案。")
        return

    print(f"找到 {len(files_to_process)} 個檔案 (.txt 或 .md)，準備開始翻譯...")

    for rel_path in tqdm(files_to_process, desc="翻譯進度"):
        source_path = os.path.join(SOURCE_FOLDER, rel_path)
        target_path = os.path.join(TARGET_FOLDER, rel_path)

        # 確保目標資料夾的子目錄存在
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 斷點續傳邏輯
        if os.path.exists(target_path):
            print(f"\n檔案已存在，跳過: {rel_path}")
            continue

        print(f"\n正在翻譯: {rel_path}")
        success = translate_file(source_path, target_path)
        if not success:
            print(f"暫停處理：{rel_path}")
            
    print("\n任務完成！請至 regular_trans_ok 資料夾查看結果。")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"本次翻譯總耗時: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main()
