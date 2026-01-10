

def transform_to_text(result: dict):
    text = ""

    for i in result:
        text += (str(i) + "\n")
        val = result[i]
        if isinstance(val, list):
            for item in val:
                text += (str(item) + "\n")
        else:
            text += (str(val) + "\n")
    
    return text


def save_to_file(save_file: str, text: str):
    try:
        with open(save_file, "w", encoding="utf-8") as file:
            file.write(text)
        print("檔案儲存成功！")
    except Exception as e:
        print(f"檔案儲存失敗：{e}")


def save_to_csv(save_file: str, df):
    try:
        df.to_csv(save_file, index=False, encoding="utf-8-sig")
        print("CSV檔案儲存成功！")
    except Exception as e:
        print(f"CSV檔案儲存失敗：{e}")
