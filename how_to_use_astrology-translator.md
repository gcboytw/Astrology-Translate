# 如何建立與使用 Astrology-Translator 模型

本指南說明如何將您的 `translation_config.py` 與 `astrology_data.py` 打包成一個專屬的 Ollama 模型 (Agent Skill)，以提升翻譯效率與一致性。

## 1. 產生 Modelfile

首先，我們需要將現有的 Python 設定檔轉換為 Ollama 看得懂的 `Modelfile` 格式。我已經準備好了一個腳本來自動完成這件事。

請在終端機執行：

```bash
python3 build_modelfile.py
```

執行後，您的目錄下會出現一個名為 `Modelfile` 的新檔案。

> **注意**：如果不執行此步驟，也可以手動編輯 `Modelfile`，但使用腳本可以確保它永遠與您的 Python 設定同步。

## 2. 建立自定義模型

使用 Ollama 的 `create` 指令來封裝模型。您可以隨意命名模型，這裡我們使用 `astrology-translator`。

請在終端機執行：

```bash
ollama create astrology-translator -f Modelfile
```

等待進度條跑完，看到 `success` 即代表建立完成。

## 3. 修改設定檔以使用新模型

模型建立好後，它已經「內建」了所有的 System Prompt 和 Glossary。您現在可以簡化您的 Python 設定了。

請打開 `translation_config.py` 並進行以下兩個修改：

1.  **修改模型名稱**：
    將 `MODEL_NAME` 改為您的新模型名稱。
    ```python
    MODEL_NAME = 'astrology-translator'
    ```

2.  **清空 System Prompt**：
    因為模型已經內化了這些規則，Python 這邊就不需要再傳送一次了（省 token 也省時間）。
    ```python
    SYSTEM_PROMPT = "" 
    ```
    *(或者您也可以保留它作為「額外補充指令」，模型會同時參考兩者，但通常清空即可)*

## 4. 開始翻譯

現在，您可以像往常一樣執行翻譯腳本，它就會使用這個專屬的占星翻譯大腦了：

```bash
python3 trans_mixed.py
```

## 常見問題 (FAQ)

### Q: 如果我有新的占星詞彙要加入怎麼辦？
1.  修改 `astrology_data.py` 加入新詞彙。
2.  重新執行 `python3 build_modelfile.py` 更新 Modelfile。
3.  重新執行 `ollama create astrology-translator -f Modelfile` 重建模型。
    *(Ollama 會自動偵測變更並更新，不用擔心)*

它不會一直佔用記憶體 (RAM)。 翻譯工作結束後，Ollama 預設會在閒置一段時間（通常是 5 分鐘）後自動把模型從記憶體中卸載（Unload），釋放資源。