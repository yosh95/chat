#!/usr/bin/env python3

import json
import llm_cli
import mimetypes
import os
import requests
import time

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY is None:
    print("GOOGLE_API_KEY environment variable must be set.")
    exit(1)
MODEL = os.getenv("GEMINI_MODEL")
if MODEL is None:
    print("GEMINI_MODEL environment variable must be set.")
    exit(1)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/" \
        + MODEL + ":generateContent?key=" + API_KEY
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files" \
        + "?key=" + API_KEY
FILES_URL = "https://generativelanguage.googleapis.com/v1beta/files"


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
                if 'file_url' in item:
                    user_message['parts'].append({
                        "file_data": {
                            "mime_type": item['content_type'],
                            "file_uri": item['file_url']
                        }
                    })
                else:
                    user_message['parts'].append({
                        "inlineData": {
                            "mimeType": item['content_type'],
                            "data": item['content']
                        }
                    })

        messages.append(user_message)
        self.write_chat_log(user_message)
        if conversation is not None:
            conversation.append(user_message)

        content = ''
        grounding_chunks = None
        try:
            headers = {
                'Content-Type': 'application/json',
            }

            data = {
                'contents': messages
            }

            if self.grounding is True:
                data['tools'] = [{'google_search': {}}]

            response = requests.post(API_URL,
                                     headers=headers,
                                     data=json.dumps(data))

            self.write_request_debug_log(headers, data, response)

            if response.status_code != 200:
                json_str = json.dumps(response.json(),
                                      ensure_ascii=False,
                                      indent=2)
                print(json_str)
                return None, None, None

            result = response.json()

            if 'content' in result['candidates'][0]:
                content = \
                    result['candidates'][0]['content']['parts'][0]['text']
                content = content.rstrip(" \n")
                if content.startswith("'content'"):
                    print(content)
                model_message = {"role": "model", "parts": [{"text": content}]}

                if 'groundingMetadata' in result['candidates'][0]:
                    gr_metadata = result['candidates'][0]['groundingMetadata']
                    if 'groundingChunks' in gr_metadata:
                        grounding_chunks = gr_metadata['groundingChunks']

            else:
                content = "ERROR: Failed to get contents in the response. " \
                     + f"Reason: {result['candidates'][0]['finishReason']}"
                model_message = {"role": "model", "parts": [{"text": content}]}

            usage = result['usageMetadata']

            self.write_chat_log(model_message)
            if conversation is not None:
                conversation.append(model_message)

        except Exception as e:
            print(f"ERROR:{e}")
            return None, None, None
        return content, usage, grounding_chunks

    def _upload_file(self, path):

        # --- 1. Determine MIME Type and File Size ---
        mime_type = mimetypes.guess_type(path)[0]
        if mime_type is None:
            print(f"Error: Could not determine MIME type for {path}")
            return None, None
        num_bytes = os.path.getsize(path)
        display_name = os.path.basename(path)

        # --- 2. Initiate Resumable Upload ---
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(num_bytes),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        }
        data = {"file": {"display_name": display_name}}

        try:
            response = requests.post(UPLOAD_URL,
                                     headers=headers,
                                     json=data, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error initiating upload: {e}")
            return None, None

        upload_url = response.headers.get("X-Goog-Upload-URL")
        if not upload_url:
            print("Error: 'X-Goog-Upload-URL' not found in response headers.")
            print("Response Headers:", response.headers)
            return None, None

        # --- 3. Upload the Data ---
        upload_headers = {
            "Content-Length": str(num_bytes),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        }

        try:
            with open(path, "rb") as f:
                response = requests.post(upload_url,
                                         headers=upload_headers,
                                         data=f,
                                         timeout=300)
                response.raise_for_status()
                file_info = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error uploading video data: {e}")
            return None, None

        # --- 4. Check File Status and Wait for Processing ---
        file_uri = file_info.get("file", {}).get("uri")
        if not file_uri:
            print("Error: 'file.uri' not found in file_info.")
            print("file_info:", file_info)
            return None, None

        state = file_info.get("file", {}).get("state")
        if not state:
            print("Error: 'file.state' not found.")
            return None, None

        name = file_uri.split('/')[-1]
        while state == "PROCESSING":
            print("Processing file...")
            time.sleep(3)
            try:
                response = requests.get(f"{FILES_URL}/{name}?key={API_KEY}",
                                        timeout=10)
                response.raise_for_status()
                file_info = response.json()
                state = file_info.get("file", {}).get("state")
            except requests.exceptions.RequestException as e:
                print(f"Error checking file status: {e}")
                return None, None

        print(f"Uploaded file url: {file_uri}")
        return file_uri, num_bytes


# CLI Interface
if __name__ == "__main__":
    gemini = Gemini(MODEL)
    gemini.main()
