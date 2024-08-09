# Description: 這個檔案是用來定義所有的工具，每一個工具都是一個 dictionary，裡面包含了工具的名稱、描述、參數等等資訊。
tools_list = [
    {"type": "file_search"},
    {
        "type": "function",
        "function": {
            'name': 'get_today_date',
            'description': '如果使用者詢問今天日期，call this function 來取得今天的日期',
        }
    },
    {
        "type": "function",
        "function": {
            'name': 'user_say_newbooks',
            'description': '如果使用者詢問有新書，call this function 來回應使用者',
        }
    },
    {
        "type": "function",
        "function": {
            'name': 'user_say_name',
            'description': '如果使用者詢問名字，call this function 來回應使用者',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': '那個使用者的名字'
                    }
                },
                'required': ['name']
            }
        }
    },
]
