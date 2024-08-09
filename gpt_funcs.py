import json
import time
import re
import os
from dotenv import load_dotenv
from tools_list import tools_list
import datetime


# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數中讀取 GPT_FILE_VECTOR_STORE_ID
gpt_file_vector_store_id = os.getenv("GPT_FILE_VECTOR_STORE_ID")


# 讀取書單內容
with open("booklist.txt", "r", encoding='utf-8') as file:
    menu = file.read().strip()


# 定義移除來源資訊的函式【8:0†source】
def remove_source_annotations(text):
    pattern = re.compile(r'【\d+:\d+†source】')
    cleaned_text = pattern.sub('', text)
    return cleaned_text


GPT_MODEL = "gpt-4o"
ASSISTANT_NAME = "文書店客服"
ASSISTANT_INSTRUCTIONS = "你是一位文書店客服，請一律使用繁體中文回答問題，請依照我們的書單內容回答，書單內容請讀取檔案:booklist.txt"
ASSISTANT_INSTRUCTION_WHEN_RUN = "你是一位文書店客服，請一律使用繁體中文回答問題，請依照我們的書單內容回答，書單內容請讀取檔案:booklist.txt"
GPT_FILE_VECTOR_STORE_ID = gpt_file_vector_store_id

# Step 1: Create an assistant


def create_assistant(client):
    assistant = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=ASSISTANT_INSTRUCTIONS,
        tools=tools_list,
        model=GPT_MODEL
    )
    return assistant.id

# 更新助手


def update_assistant(client, assistant_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {
            "vector_store_ids": [GPT_FILE_VECTOR_STORE_ID]}},
    )


# Step 2: Create a Thread
def create_thread(client):
    my_thread = client.beta.threads.create()
    print('thread created, thread_id:', my_thread.id)
    return my_thread.id


# Step 3: Add a Message to a Thread
def add_user_message_to_thread(client, thread_id, msg):
    user_message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=msg,
    )
    return user_message


def get_today_date():
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    return today_str

#


def user_say_newbooks():
    return "趕緊推薦使用者 2024 年最新的書單。"


def user_say_name(name):
    # 把使用者的名字加入回應中
    print("使用者的名字是:", name)
    return f"請明確告知使用者，{name}，您想要找什麼書。"


# Step 4: Run
def wait_for_assistant_run(client, thread_id, assistant_id):
    assistant_r = None
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=ASSISTANT_INSTRUCTION_WHEN_RUN
    )
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        print(f'Run status: {run.status}')
        time.sleep(1)
        if run.status == "completed":
            all_messages = client.beta.threads.messages.list(
                thread_id=thread_id
            )
            assistant_r = all_messages.data[0].content[0].text.value
            assistant_r = remove_source_annotations(assistant_r)
            print(f'Assistant: {assistant_r}')
            break
        elif run.status == 'requires_action':
            required_actions = run.required_action.submit_tool_outputs.model_dump()
            print(required_actions)
            tool_outputs = []

            for action in required_actions["tool_calls"]:
                func_name = action['function']['name']
                print('Assistant required action:', func_name)
                if action['function']['arguments']:
                    arguments = json.loads(action['function']['arguments'])
                # call func
                if func_name == 'get_today_date':
                    output = get_today_date()
                if func_name == 'user_say_weather':
                    output = user_say_newbooks()
                if func_name == 'user_say_name':
                    output = user_say_name(arguments['name'])
                else:
                    output = 'Function not found'

                tool_outputs.append({
                    "tool_call_id": action['id'],
                    "output": output
                })

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
        elif run.status == 'queued' or run.status == 'in_progress':
            pass
        else:
            print(f'Run status: {run.status}')
            print('create_and_poll again')
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=ASSISTANT_INSTRUCTION_WHEN_RUN
            )

    return assistant_r
