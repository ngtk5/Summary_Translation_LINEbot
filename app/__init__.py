from os import environ
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, Source, TextMessage, TextSendMessage

from app.deepl.deepl_api import DeepLAPI
from app.gpt.client import ChatGPTClient
from app.gpt.constants import Model, Role
from app.gpt.message import Message

# 参考サイトURL：https://qiita.com/nanato12/items/4b735b4d95abf2fdb554

load_dotenv(".env", verbose=True)

app = Flask(__name__)

if not (access_token := environ.get("LINE_CHANNEL_ACCESS_TOKEN")):
    raise Exception("access token is not set as an environment variable")

if not (channel_secret := environ.get("LINE_CHANNEL_SECRET")):
    raise Exception("channel secret is not set as an environment variable")

if not (deepl_api_key := environ.get("DEEPL_API_KEY")):
    raise Exception("deepl api key is not set as an environment variable")

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret)

chatgpt_instance_map: Dict[str, ChatGPTClient] = {}
deepl_api = DeepLAPI(deepl_api_key)


@app.route("/callback", methods=["POST"])
def callback() -> str:
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent) -> None:
    text_message: TextMessage = event.message
    source: Source = event.source
    user_id: str = source.user_id
    res_text: str = ""

    if (gpt_client := chatgpt_instance_map.get(user_id)) is None:
        gpt_client = ChatGPTClient(model=Model.GPT35TURBO)

    # ユーザから"/new chat"メッセージを受け取った場合
    # 会話履歴を削除する(≒新たな会話を開始する)
    if text_message.text == "/new chat":
        # ChatGPTClientインスタンスのmessages属性を空のリストにする
        gpt_client = chatgpt_instance_map.get(user_id)
        if gpt_client:
            gpt_client.messages = []
            res_text = "今までの会話履歴を削除しました。\n新たな会話を始めます。"
    elif text_message.text == "/set en":
        deepl_api.set_target_lang_to_en()
        res_text = "翻訳先言語を英語に設定しました。"
    elif text_message.text == "/set ja":
        deepl_api.set_target_lang_to_ja()
        res_text = "翻訳先言語を日本語に設定しました。"
    else:
        send_message = f"以下の文章を要約してください。" \
            f"\n{text_message.text}"
        gpt_client.add_message(
            message=Message(role=Role.USER, content=send_message)
        )
        res = gpt_client.create()
        res_text = deepl_api.translation(res["choices"][0]["message"]["content"])

    chatgpt_instance_map[user_id] = gpt_client
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=res_text.strip())
    )
