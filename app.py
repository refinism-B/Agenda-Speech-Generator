import os
import gradio as gr
import pandas as pd
from src.mod import A_LLM as lmp
from src.mod import B_text as tp

# 設定暫存資料夾
TEMP_DIR = "temp_output"
os.makedirs(TEMP_DIR, exist_ok=True)

def generate_agenda(url_input, file_input):
    """
    主要處理函式：接收輸入 -> 讀取內容 -> LLM 生成 -> 回傳預覽與下載檔案路徑
    """
    try:
        # 1. 讀取內容
        if file_input:
            content = lmp.load_content(source=file_input, source_type='file')
        elif url_input:
            content = lmp.load_content(source=url_input, source_type='url')
        else:
            return pd.DataFrame(), "錯誤：請輸入網址或上傳檔案", None, None

        if not content or "錯誤" in content:
             return pd.DataFrame(), f"讀取失敗或內容為空: {content}", None, None

        # 2. 選擇LLM模型並連線
        model_name = 'gemini-3-flash-preview' # 更新模型名稱以獲得更好效能，或維持 'gemini-1.5-flash'
        llm = lmp.connect_llm_model(model_name=model_name)

        # 3. 建立prompt及相關資料
        prompt_template = lmp.create_prompt_template()
        json_parser, data = lmp.create_prompt_data(content=content)

        # 4. 建立chain並啟動
        llm_chain = prompt_template | llm
        
        # 顯示處理中（Gradio 會自動顯示 spinner，但在這裡我們可以 print log）
        print("開始執行 LLM 生成...")
        ai_message = llm_chain.invoke(data)
        
        try:
            response = json_parser.invoke(ai_message)
        except Exception as e:
            # 如果解析失敗，回傳原始訊息供參考
            return pd.DataFrame(), f"解析失敗，LLM 回應: {ai_message.content}\n錯誤: {e}", None, None

        input_token, out_token = lmp.get_tokens_info(ai_message=ai_message)
        print(f"輸入token: {input_token}, 輸出token: {out_token}")

        # 5. 預覽輸出結果
        df = lmp.transform_to_df(response=response, key="agendas")

        # 6. 產生下載檔案
        txt_content = tp.transform_to_text(result=response)
        
        # 產生存檔路徑
        csv_path = os.path.join(TEMP_DIR, "agenda_output.csv")
        txt_path = os.path.join(TEMP_DIR, "agenda_output.txt")
        
        tp.save_to_csv(csv_path, df)
        tp.save_to_file(txt_path, txt_content)

        token_info = f"Token 使用量 - Input: {input_token}, Output: {out_token}"
        
        return df, token_info, csv_path, txt_path

    except Exception as e:
        return pd.DataFrame(), f"系統發生錯誤: {str(e)}", None, None

# Gradio 介面設計
custom_css = """
/* Global Text (+4px - 2px = +2px -> 18px) */
.gradio-container {
    font-size: 18px !important;
}
/* Ensure standard elements inherit or use this size */
.gradio-container p, .gradio-container span, .gradio-container label, .gradio-container input, .gradio-container button {
    font-size: 18px;
}

/* Main Title (+8px - 2px -> 38px) & Centered */
#main-title h1 {
    font-size: 38px !important;
    text-align: center;
    margin-bottom: 0.5rem;
}

/* Description (+8px - 2px -> 22px) & Centered */
#description {
    font-size: 22px !important;
    text-align: center;
}

/* Tab Labels (+6px - 2px -> 20px) */
.tab-nav button {
    font-size: 20px !important;
}
"""

with gr.Blocks(title="Agenda Speech Generator", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# 🎤 活動議程司儀稿生成器", elem_id="main-title")
    gr.Markdown("輸入活動網頁或上傳議程檔案，自動生成標準司儀稿。", elem_id="description")
    
    with gr.Tabs():
        with gr.TabItem("Web URL"):
            url_input = gr.Textbox(label="請輸入活動網址", placeholder="https://example.com/agenda")
            # 隱藏的 Type 標記
            
        with gr.TabItem("File Upload"):
            file_input = gr.File(label="請上傳檔案", file_types=[".pdf", ".txt", ".csv", ".xlsx", ".docx", ".md"])


    

    
    submit_btn = gr.Button("開始生成", variant="primary")
    
    gr.Markdown("### 結果預覽")
    output_df = gr.DataFrame(label="議程表預覽")
    status_msg = gr.Textbox(label="執行狀態/Token資訊", interactive=False)
    
    with gr.Row():
        csv_download = gr.File(label="下載 CSV", interactive=False)
        txt_download = gr.File(label="下載 TXT", interactive=False)
    
    # 事件綁定
    submit_btn.click(
        fn=generate_agenda,
        inputs=[url_input, file_input],
        outputs=[output_df, status_msg, csv_download, txt_download]
    )

if __name__ == "__main__":
    demo.launch()