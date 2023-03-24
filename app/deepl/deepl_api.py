import requests


class DeepLAPI:
    def __init__(self, key: str):
        # DeepL APIのURLとAPIキー
        self.url: str = "https://api-free.deepl.com/v2/translate"
        self.api_key: str = key
        self.target_lang: str = "en"

    def translation(self, text: str) -> str:
        # HTTPリクエストを送信して翻訳を取得する
        response = requests.post(self.url, data={
            "auth_key": self.api_key,
            "text": text,
            "target_lang": self.target_lang,
        })
        # 翻訳結果を取得する
        translated: str = response.json()["translations"][0]["text"]

        return translated

    def set_target_lang_to_en(self):
        self.target_lang = "en"

    def set_target_lang_to_ja(self):
        self.target_lang = "ja"
