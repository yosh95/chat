#!/usr/bin/env python3

import chat
import json
import os
import requests

API_KEY = os.getenv("OPENAI_API_KEY", "")
API_URL = 'https://api.openai.com/v1/chat/completions'
MODEL = os.getenv("O1_MODEL", "o1-preview")


class O1(chat.Chat):

    def _send(self, data, conversation):

        if conversation is None:
            messages = []
        else:
            messages = list(conversation)

        user_message = {
            "role": "user",
            "content": [
            ]}
        for item in data:
            if 'content_type' not in item or \
                    item['content_type'] is None or \
                    'text' in item['content_type']:
                user_message['content'].append({
                    "type": "text",
                    "text": item['content']
                })
            else:
                image_url = f"data:{item['content_type']}"
                image_url += f";base64,{item['content']}"
                user_message['content'].append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                })

        messages.append(user_message)

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {API_KEY}',
            }

            data = {
                'model': MODEL,
                'messages': messages,
            }

            content = ''

            response = requests.post(API_URL,
                                     headers=headers,
                                     data=json.dumps(data))

            self.write_request_debug_log(headers, data, response)

            response.raise_for_status()

            result = response.json()

            content = result['choices'][0]['message']['content']

            usage = result['usage']

            model_message = {"role": "assistant", "content": content}
            if conversation is not None:
                conversation.append(user_message)
                conversation.append(model_message)

        except Exception as e:
            print(e)
            return None, None
        return content, usage


if __name__ == "__main__":
    o1 = O1(MODEL)
    o1.main()
