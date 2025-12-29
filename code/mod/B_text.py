

def transform_to_text(result: dict):
    text = ""

    for i in result:
        text += (i + "\n")
        text += (result[i] + "\n")

    return text


def save_to_file(save_file: str, text: str):
    try:
        with open(save_file, "w", encoding="utf-8") as file:
            file.write(text)
        print("檔案儲存成功！")
    except Exception as e:
        print(f"檔案儲存失敗：{e}")
