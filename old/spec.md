沒問題，我為你整理了一份完整的 `spec.md`。這份文件包含了環境配置、資料夾結構以及你要求的自動化工作流邏輯，你可以直接複製並儲存為檔案。

---

```markdown
# 占星語音轉錄與校正系統技術規格書 (Spec)

## 1. 專案概述
本專案旨在 Windows 平台上建立一套自動化工作流，利用 `faster-whisper` 進行高品質語音轉錄，並結合 `Ollama` 進行占星專業術語校正，最終產出符合筆記需求的 Markdown 與 SRT 字幕檔案。

## 2. 環境需求
- **作業系統**: Windows 10/11
- **Python 版本**: 3.9 或以上
- **核心依賴**:
    - `faster-whisper`: 語音轉文字引擎
    - `ollama`: 呼叫本地 LLM (如 Gemma 3) 進行文字校正
    - `pysrt`: (選配) 若需精細處理 SRT 格式

## 3. 資料夾結構預設
```text
Astrology-Transcribe/
├── models/
│   └── whisper-large-v3/      # 指定模型存放路徑
├── output/
│   ├── [filename].srt         # 校正後字幕檔
│   └── [filename].md          # 校正後筆記檔 (原 txt 格式)
├── astrology_data.py          # 存放 Glossary 名詞庫
├── transcribe_engine.py       # 主程式腳本
└── input_audio.mp3            # 待處理音檔

```

## 4. 技術流程規格

### Step 1: 模型初始化

* **模型選擇**: 使用 OpenAI Whisper `large-v3` 版本。
* **儲存設定**: 程式啟動時需檢查 `./models/whisper-large-v3`，若無模型則自動下載至該路徑。
* **運算設定**: 預設使用 `device="cpu"`，若偵測到 CUDA 環境則切換至 `cuda`。

### Step 2: 轉錄階段 (Whisper)

* **語音引導 (Prompting)**:
* 加入 `initial_prompt`: "相位、合相、三分相、六分相、四分相、對相、宮位"。


* **VAD 偵測**: 開啟語音活動偵測 (Voice Activity Detection)，自動過濾背景噪音與空白段。

### Step 3: 校正階段 (Ollama)

* **外部資料庫**: 讀取 `astrology_data.py` 中的 `glossary` 列表。
* **校正邏輯**:
* 針對 Whisper 產出的 Segment 進行逐段或批量校正。
* 修正同音異字（如：「合相」誤植為「河相」）。



### Step 4: 輸出規格

* **SRT 格式**: 保留標準時間標籤與校正後的文本。
* **Markdown 格式**:
* 取代原有的 `.txt` 格式。
* 使用 `### [時間戳]` 作為標題層級。
* 內容需包含校正後的完整逐字稿。



## 5. 快速安裝指令

```bash
pip install faster-whisper ollama

```

## 6. 後續擴展建議

* 增加批次處理功能（一次轉換整個資料夾的音檔）。
* 整合 GPU 加速驅動 (NVIDIA CUDA 12.x)。
