import os
import ollama
from tqdm import tqdm
from datetime import datetime
import time

# --- 專用設定區 ---
# 這裡直接指定我們要用的 "Custom Model"
MODEL_NAME = 'astrology-translator'

# 來源與目標資料夾 (可以跟原本共用，也可以改)
SOURCE_FOLDER = 'need_trans_txt'
TARGET_FOLDER = 'trans_ok_md'
CHUNK_SIZE = 3000

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
        if current_length + len(line) > max_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(line)
        current_length += len(line) + 1 
        
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks

def translate_chunk(chunk_text, index, total):
    """
    翻譯單一文本塊
    """
    # 這裡的 Prompt 可以非常簡短，因為 System Prompt 已經內建在模型裡了
    prompt = f"Part {index}/{total}:\n{chunk_text}"

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            # system=,  <-- 這裡不需要傳 System Prompt，因為模型本身就有
            prompt=prompt,
            options={
                'temperature': 0.3,
                'num_ctx': 8192,
            }
        )
        return response['response']
    except Exception as e:
        print(f"\n[錯誤] 翻譯片段 {index} 時發生問題: {e}")
        return None

def translate_file(file_path, output_path):
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

    chunks = split_text_into_chunks(content, CHUNK_SIZE)
    if not chunks:
        print(f"[警告] 檔案 {file_path} 內容似乎為空。")
        return False

    translated_parts = []
    print(f"  - 檔案較大，已分割為 {len(chunks)} 個片段進行翻譯...")

    for i, chunk in enumerate(chunks, 1):
        print(f"    轉換中... ({i}/{len(chunks)})")
        translated_part = translate_chunk(chunk, i, len(chunks))
        
        if translated_part:
            translated_parts.append(translated_part)
        else:
            print(f"    [失敗] 片段 {i} 翻譯失敗，將保留原文佔位。")
            translated_parts.append(f"\n\n[Translation Failed for Chunk {i}]\n\n{chunk}\n\n")

    final_text = '\n\n'.join(translated_parts)
    
    # 添加 Obsidian YAML tags
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yaml_header = f"---\ncreated: {now}\ntags: [astrology]\nmodel: {MODEL_NAME}\n---\n\n"
    final_text = yaml_header + final_text
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    return True

def main():
    start_time = time.time()

    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"已建立目標資料夾: {TARGET_FOLDER}")

    # 檢查是否已經建立了模型
    try:
        models = ollama.list()
        # ollama.list() 返回的是 Object 列表，需要檢查 name 屬性
        # 注意：不同版本的 ollama SDK 返回結構可能不同，這裡做簡單的字串檢查
        model_exists = False
        for m in models['models']:
            if MODEL_NAME in m['name']:
                model_exists = True
                break
        
        if not model_exists:
            print(f"⚠️  警告：找不到模型 '{MODEL_NAME}'")
            print(f"請先執行： ollama create {MODEL_NAME} -f Modelfile")
            print("程式將嘗試繼續，但可能會失敗...")
    except Exception:
        pass # 如果檢查失敗就不管了，直接跑跑看

    files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith('.txt')]
    files.sort()

    print(f"找到 {len(files)} 個檔案，準備使用專屬模型 '{MODEL_NAME}' 進行翻譯...")

    for file_name in tqdm(files, desc="翻譯進度"):
        source_path = os.path.join(SOURCE_FOLDER, file_name)
        target_path = os.path.join(TARGET_FOLDER, file_name.replace('.txt', '.md'))

        if os.path.exists(target_path):
            print(f"檔案已存在，跳過: {file_name}")
            continue

        print(f"\n正在翻譯: {file_name}")
        success = translate_file(source_path, target_path)
        if not success:
            print(f"暫停處理：{file_name}")
            
    print("\n任務完成！請至 trans_ok_md 資料夾查看結果。")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"本次翻譯總耗時: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main()
