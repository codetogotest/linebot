import os

# 引入 Flask 套件
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# 引入 OpenAI client 和相關函數
from openai import OpenAI
from linebot.v3.webhook import WebhookHandler  # 引入 WebhookHandler
from gpt_funcs import create_assistant, create_thread,  add_user_message_to_thread, wait_for_assistant_run, update_assistant
from dotenv import load_dotenv  # 引入 load_dotenv

load_dotenv()  # 載入 .env 檔案

api_key = os.getenv("OPENAI_API_KEY")

# 從環境變數中讀取 access_token 和 handler key
access_token = os.getenv('LINEBOT_ACCESS_TOKEN')
handler_key = os.getenv('HANDLER_KEY')

# 建立 OpenAI client
client = OpenAI(api_key=api_key)

# 建立 assistant 和 thread
assistant_id = create_assistant(client)
update_assistant(client, assistant_id)
thread_id = create_thread(client)

# 建立 Flask app
app = Flask(__name__)

# 建立 Line Messaging API client
configuration = Configuration(access_token=access_token)
handler = WebhookHandler(handler_key)

# 設定 webhook route


@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# 設定 message event handler


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text
    add_user_message_to_thread(client, thread_id, user_msg)
    assistant_r = wait_for_assistant_run(client, thread_id, assistant_id)

    # 回覆使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        r = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=assistant_r)]
        )
        line_bot_api.reply_message_with_http_info(r)


# 啟動 Flask app
if __name__ == "__main__":
    app.run()
