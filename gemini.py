#!/usr/bin/env python3

import chat
import json
import os
import requests

MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
API_KEY = os.getenv("GEMINI_API_KEY", "")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/" \
           + MODEL + ":generateContent?key=" + API_KEY
SAFETY_SETTING = os.getenv("GEMINI_SAFETY_SETTING",
                           "HARM_BLOCK_THRESHOLD_UNSPECIFIED")


class Gemini(chat.Chat):

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

        content = ''
        try:
            headers = {
                'Content-Type': 'application/json',
            }

            data = {
                'contents': messages
            }

            data['safety_settings'] = [
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": SAFETY_SETTING
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": SAFETY_SETTING
                },
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": SAFETY_SETTING
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": SAFETY_SETTING
                }
            ]

            response = requests.post(API_URL,
                                     headers=headers,
                                     data=json.dumps(data))

            self.write_request_debug_log(headers, data, response)

            response.raise_for_status()

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
                conversation.append(user_message)
                conversation.append(model_message)

        except Exception as e:
            print(e)
            return None, None
        return content, usage


# CLI Interface
if __name__ == "__main__":
    gemini = Gemini(MODEL)
    gemini.main()
