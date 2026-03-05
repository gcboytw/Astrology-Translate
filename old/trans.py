import os
import ollama
from tqdm import tqdm
from datetime import datetime
import time

# --- 設定區 ---
SOURCE_FOLDER = 'need_trans_txt'
TARGET_FOLDER = 'trans_ok_md'
MODEL_NAME = 'translategemma:12b'
CHUNK_SIZE = 3000  # 每次處理的字元數限制，確保不超過 Context Window
SERIES_THEME ="處女座 (Virgo) 的完美追求與服務精神"

GLOSSARY = {
    "Ascendant": "上升星座",
    "Midheaven": "天頂",
    "Aspects": "相位",
    "Conjunction": "合相",
    "Opposition": "對分相 (沖)",
    "Trine": "三分相 (拱)",
    "Square": "四分相 (刑)",
    "Sextile": "六分相",
    "Retrograde": "逆行",
    "Aries": "白羊座",
    "Capricorn": "磨羯座",
    "House": "宮位",
    
    # --- 本系列專用 (SERIES) - ---
    "Virgo": "處女座",
    "Mercury": "水星", # 處女座守護星
    "Mutable Earth": "變動土象",
    "The Virgin": "處女/室女", # 象徵圖騰
    "Virgo Man": "處女男",
    "Virgo Woman": "處女女",
    "Virgo Boss": "處女老闆",
    "Virgo Employee": "處女員工",
    "Virgo Baby": "處女孩童",
    "Perfectionist": "完美主義者",
    "Analysis": "分析",
    "Critical": "挑剔/批判性",
    "Service": "服務",
    "Discrimination": "辨識力/鑑賞力",
}

# 系統指令：整合你的 Skill 規則
SYSTEM_PROMPT = f"""
Role: 你是一位專業的占星學翻譯專家。針對本次系列主題為：「{SERIES_THEME}」。
你具備深厚的占星背景知識，能精準處理相位、宮位及行星相位組成的專有名詞。
Target Language: 繁體中文 (Traditional Chinese, Taiwan Standard)
Background & Style:
- 目標讀者：專業占星研習者與研究員。
- 語氣：優雅、專業、具有玄學美感但邏輯嚴密。要像在讀林樂卿（Linda Goodman）或其他占星名家的中文經典譯作。
- 語感：翻譯應呈現中文的自然律動，避免名詞堆疊，多用主動句式，少用「被...」等被動語態。
- 規則：
1. **譯名標準**：優先使用台灣占星慣用譯名。
   - Aries -> 白羊座（而非牡羊座）
   - Capricorn -> 磨羯座（而非山羊座）
   - House -> 宮位（嚴禁譯為房子，必須根據上下文翻譯為「宮位」）
2. **術語處理**：不確定的古老術語請保留原文並括號標註，如：Hyleg (希利格點)。
3.  **語序優化 (核心)**：
   - 嚴禁直譯 "That figures" 為「這很正常」，應譯為「這不意外」或「這很符合其個性」。
   - 嚴禁保留英文倒裝句法。請將後置的條件、原因或修飾子句根據中文習慣調整至句首，或轉化為流暢的獨立句。
   - 重新排列條件句：將原文後置的 if 子句移至動作發生前。
   - 避免「進行對話」、「感到害羞」等冗贅動詞，改用「回擊」、「羞於」、「直言不諱」等精確動詞。
4. **長句拆解**：遇到結構複雜的長句，請在不遺漏原意的前提下進行拆解，避免產生冗長且難懂的複合句。
5. **格式保持**：完整保留星盤符號、表格與段落結構。
6. **內容完整**：精準還原原意，嚴禁摘要或刪減內容。
7. **修辭增強**：
   - 善用四字成語或穩重的中文慣用語（如：義憤填膺、直截了當、毫不猶豫、無關緊要）。
   - 針對占星語境進行「修辭優化」
8. **去字優化**：減少「的」字的使用次數，讓語句更為乾淨利落。
9. **拒絕機器感**：避免「...的人」、「...的事情」等結構。

Technical Glossary:
{GLOSSARY}

Mandatory: 請確保輸出內容完全為繁體中文，且讀起來像是台灣占星師親筆撰寫的專業文案。
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

def translate_chunk(chunk_text, index, total):
    """
    翻譯單一文本塊
    """
    # 提示詞中加入這是第幾部分的資訊，幫助模型理解上下文連續性 (雖然模型主要看的是傳入的 chunk)
    prompt = f"Please translate the following Astrology text into Traditional Chinese (Part {index}/{total}). Ensure NO simplified Chinese characters are used Translate fully and accurately:\n\n{chunk_text}"

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
                'repeat_penalty': 1.1, # 稍微增加處罰，防止 12b 在長文翻譯中出現重複句式。
            }
        )
        return response['response']
    except Exception as e:
        print(f"\n[錯誤] 翻譯片段 {index} 時發生問題: {e}")
        return None

def translate_file(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 切割文本
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

    # 建立目標資料夾
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"已建立目標資料夾: {TARGET_FOLDER}")

    # 讀取待翻譯檔案清單
    files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith('.txt')]
    files.sort() # 確保按章節順序處理

    print(f"找到 {len(files)} 個檔案，準備開始翻譯...")

    for file_name in tqdm(files, desc="翻譯進度"):
        source_path = os.path.join(SOURCE_FOLDER, file_name)
        #target_path = os.path.join(TARGET_FOLDER, file_name)
        target_path = os.path.join(TARGET_FOLDER, file_name.replace('.txt', '.md'))

        # 斷點續傳邏輯
        if os.path.exists(target_path):
            print(f"檔案已存在，跳過: {file_name}")
            continue

        print(f"\n正在翻譯: {file_name}")
        success = translate_file(source_path, target_path)
        if not success:
            print(f"暫停處理：{file_name}")
            # 視需求決定是否中斷，這裡選擇繼續下一個
            # break 
            
    print("\n任務完成！請至 trans_ok_md 資料夾查看結果。")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"本次翻譯總耗時: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main()