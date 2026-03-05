# -*- coding: utf-8 -*-
"""
Build Modelfile Script
此腳本會讀取 translation_config.py 中的設定 (包含完整的 System Prompt 與 Glossary)，
並產生一個 Ollama 專用的 Modelfile。
"""

from translation_config import SYSTEM_PROMPT, MODEL_NAME

def main():
    # 定義新的模型名稱 (你可以自訂)
    NEW_MODEL_NAME = "astrology-translator"

    # 組合 Modelfile 內容
    # 使用 3 個引號包住 System Prompt 以確保格式正確
    modelfile_content = f"""FROM {MODEL_NAME}

SYSTEM \"\"\"
{SYSTEM_PROMPT}
\"\"\"
"""

    # 寫入檔案
    with open("Modelfile", "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"✅ Modelfile 已建立完成！")
    print(f"請在終端機執行以下指令來建立自定義模型：")
    print(f"\n    ollama create {NEW_MODEL_NAME} -f Modelfile\n")
    print(f"建立完成後，你就可以在 trans_mixed.py 中把 MODEL_NAME 改為 '{NEW_MODEL_NAME}'，")
    print(f"並且把 SYSTEM_PROMPT 設為空字串 (因為已經內建在模型裡了)。")

if __name__ == "__main__":
    main()
