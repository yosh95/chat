#!/usr/bin/env python3

import llm_cli
import json
import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY is None:
    print("GEMINI_API_KEY environment variable must be set.")
    exit(1)
MODEL = os.getenv("GEMINI_MODEL")
if MODEL is None:
    print("GEMINI_MODEL environment variable must be set.")
    exit(1)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/" \
           + MODEL + ":generateContent?key=" + API_KEY

session = requests.Session()

class Gemini(llm_cli.Chat):

    def _send(self, data, conversation):

        if conversation is None:
            messages = []
        else:
            messages = list(conversation)

        user_message = {
            "role": "user",
            "parts": [
            ]}
        for item in data:
            if 'content_type' not in item or \
                    item['content_type'] is None or \
                    'text' in item['content_type']:
                user_message['parts'].append({
                    "text": item['content']
                })
            else:
                user_message['parts'].append({
                    "inlineData": {
                        "mimeType": item['content_type'],
                        "data": item['content']
                    }
                })

        messages.append(user_message)
        if conversation is not None:
            conversation.append(user_message)

        content = ''
        try:
            headers = {
                'Content-Type': 'application/json',
            }

            data = {
                'contents': messages
            }

            response = session.post(API_URL,
                                    headers=headers,
                                    data=json.dumps(data))

            self.write_request_debug_log(headers, data, response)

            if response.status_code != 200:
                json_str = json.dumps(response.json(),
                                      ensure_ascii=False,
                                      indent=2)
                print(json_str)
                return None, None

            result = response.json()

            if 'content' in result['candidates'][0]:
                content = \
                    result['candidates'][0]['content']['parts'][0]['text']
                content = content.rstrip(" \n")
                if content.startswith("'content'"):
                    print(content)
                model_message = {"role": "model", "parts": [{"text": content}]}

            else:
                content = "ERROR: Failed to get contents in the response. " \
                     + f"Reason: {result['candidates'][0]['finishReason']}"
                model_message = {"role": "model", "parts": [{"text": content}]}

            usage = result['usageMetadata']

            if conversation is not None:
                conversation.append(model_message)

        except Exception as e:
            print(f"ERROR:{e}")
            return None, None
        return content, usage


# CLI Interface
if __name__ == "__main__":
    gemini = Gemini(MODEL)
    gemini.main()
