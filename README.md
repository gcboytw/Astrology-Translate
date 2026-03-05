# 占星翻譯工具 (Astrology Translation Tool)

本專案是專為占星學文本設計的自動化翻譯工具，支援從英文翻譯至繁體中文（台灣慣用占星術語）。

## 核心腳本說明

本專案包含兩個主要的翻譯腳本，適用於不同的翻譯情境：

### 1. `trans.py` (單一系列專用)
- **用途**：適用於翻譯**單一星座專題**的書籍或一系列文章（例如：整本都在講處女座）。
- **特點**：設定較為固定。
- **設定方式**：
    - 直接修改檔案內的 `SERIES_THEME` 與 `GLOSSARY` 變數。
    - 若要切換星座，需手動從 `astrology.txt` 複製對應的資料覆蓋進去。

### 2. `trans_mixed.py` (全書混合版)
- **用途**：適用於**綜合型**的書籍或文章，內容可能同時提到 12 星座與各種相位。
- **特點**：高度模組化，讀取外部設定檔，維護容易。
- **資料來源**：自動引用 `astrology_data.py` 中的完整 12 星座大辭典。
- **設定方式**：**不需要改程式碼**，請直接修改 `translation_config.py`。

---

## 設定檔說明 (`translation_config.py`)

這是 `trans_mixed.py` 的控制中心。你可以由此調整所有參數，而無需觸碰程式邏輯。

主要可調整項目：
- **`SERIES_THEME`**：本次翻譯的主題（會影響 AI 的 System Prompt）。
- **`MODEL_NAME`**：使用的 Ollama 模型（預設 `translategemma:12b`）。
- **`SYSTEM_PROMPT`**：AI 的人設與翻譯規則（包含被動語態處理、倒裝句優化等指令）。
- **`GLOSSARY`**：指定要使用的詞彙表（預設引用 `FULL_GLOSSARY`）。

---

## 如何使用

請在終端機 (Terminal) 執行以下指令：

### 執行混合版翻譯 (推薦)
```bash
python3 trans_mixed.py
```

### 執行單一系列翻譯
```bash
python3 trans.py
```

## 檔案結構
- `trans_mixed.py`: 主程式 (混合版)
- `translation_config.py`: 設定檔 (**常用**)
- `astrology_data.py`: 占星術語資料庫 (包含 12 星座完整詞彙)
- `trans.py`: 主程式 (舊版/單一系列版)
- `need_trans_txt/`: **輸入**資料夾 (請放入英文 .txt 檔)
- `trans_ok_md/`: **輸出**資料夾 (翻譯好的 .md 檔會出現在這)
