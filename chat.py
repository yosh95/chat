#!/usr/bin/env python3

import argparse
import base64
import filetype
import json
import os
import requests
import sys

from bs4 import BeautifulSoup
from collections import deque
from dotenv import load_dotenv
from io import BytesIO
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import prompt
from pypdf import PdfReader

# Read .env
load_dotenv()

# Constants
INPUT_HISTORY = os.getenv(
        "PROMPT_HISTORY",
        f"{os.path.expanduser('~')}/.chat_prompt_history")
REQUEST_DEBUG_LOG = os.getenv(
        "REQUEST_DEBUG_LOG",
        f"{os.path.expanduser('~')}/.chat_request_debug_log")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", None)
USER_AGENT = os.getenv("USER_AGENT", "LLM_Chat_Tool")
PDF_AS_IMAGE = False

# prompt_toolkit
kb = KeyBindings()


class Chat():

    MODEL = ""

    last_usage = None

    conversation = deque()

    def __init__(self, model):
        self.MODEL = model

    @kb.add('c-j')
    def _(event):
        event.current_buffer.insert_text('\n')

    def append_to_data(self, data, content, content_type=None):
        if data is None:
            data = []
        if content_type is None:
            content_type = "text/plain"
        data.append({
            "content": content,
            "content_type": content_type
        })
        return data

    def send_and_print(self, data):
        response, self.last_usage = self._send(data, self.conversation)
        print(f"({self.MODEL}):\n{response}")

    def talk(self, data):

        if data is None:
            data = []

        prompt_history = FileHistory(INPUT_HISTORY)

        while True:

            try:
                print("----")
                user_input = prompt('> ',
                                    history=prompt_history,
                                    key_bindings=kb,
                                    enable_suspend=True,
                                    enable_system_prompt=True,
                                    enable_open_in_editor=True)
                user_input = user_input.strip()
            except UnicodeDecodeError as e:
                print(e)
                continue
            except KeyboardInterrupt:
                break
            except EOFError:
                break

            # special commands
            if user_input in ['.h', '.hist', '.history']:
                print(json.dumps(list(self.conversation),
                                 indent=2, ensure_ascii=False))
                continue

            if user_input == '':
                continue
            else:
                data = self.append_to_data(data, user_input)
                self.send_and_print(data)
            data = []

    def encode_data_from_file(self, file_path):
        with open(file_path, "rb") as data:
            return base64.b64encode(data.read()).decode('utf-8')

    def read_pdf_from_file(self, file_name):
        reader = PdfReader(file_name)
        text = ''
        for page in reader.pages:
            text += '\n' + page.extract_text()
        if text != '':
            return text
        else:
            print("Empty PDF.")
            return None

    def read_pdf_from_byte_stream(self, byte_stream):
        reader = PdfReader(byte_stream)
        text = ''
        for page in reader.pages:
            text += '\n' + page.extract_text()
        return text

    def read_text_from_file(self, file_name):
        text = ''
        with open(file_name, 'r', encoding='utf-8') as file:
            text = file.read()
        return text

    def fetch_url_content(self, url):
        headers = {}
        headers['User-Agent'] = USER_AGENT
        try:
            response = requests.get(url,
                                    headers=headers,
                                    timeout=(5.0, 5.0))
            response.raise_for_status()
        except Exception as e:
            print(e)
            return None, None

        content_type = response.headers['Content-Type']

        content = response.content

        if 'application/pdf' in content_type:
            if PDF_AS_IMAGE is True:
                return base64.b64encode(
                    BytesIO(content).read()).decode('utf-8'), content_type
            else:
                return self.read_pdf_from_byte_stream(BytesIO(content)), \
                        'text/plain'
        elif 'text/html' in content_type:
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(' ', strip=True), content_type
        elif 'text/plain' in content_type:
            return content.decode('utf-8'), content_type
        elif 'image/' in content_type:
            return base64.b64encode(
                BytesIO(content).read()).decode('utf-8'), content_type
        else:
            print(f"Unavailable content type: {content_type}")
            return None, None

    def process_sources(self, sources):
        data = []
        for source in sources:
            if source.startswith("http"):
                content, content_type = self.fetch_url_content(source)
            elif os.path.exists(source):
                content_type = None
                kind = filetype.guess(source)
                if kind and kind.extension == 'pdf':
                    if PDF_AS_IMAGE is True:
                        content = self.encode_data_from_file(source)
                    else:
                        content = self.read_pdf_from_file(source)
                    content_type = kind.mime
                elif kind and 'image/' in kind.mime:
                    content = self.encode_data_from_file(source)
                    content_type = kind.mime
                else:
                    content = self.read_text_from_file(source)
            else:
                content = source
                content_type = "text/plain"

            if content is not None:
                data.append({
                    "content": content,
                    "content_type": content_type
                })

        self.talk(data)

    def write_request_debug_log(self, headers, data, response):
        with open(REQUEST_DEBUG_LOG, 'w', encoding='utf-8') as file:
            file.write('--- (request) ---\n')
            file.write(
                "headers: "
                + f"{json.dumps(headers, ensure_ascii=False, indent=2)}\n")
            file.write(
                f"data: {json.dumps(data, ensure_ascii=False, indent=2)}\n")
            file.write('\n')
            file.write("--- (response) ---\n")
            file.write(f"status: {response.status_code}\n")
            file.write(
                "headers: "
                + f"{json.dumps(dict(response.headers), indent=2)}\n")
            json_str = response.json()
            file.write(
                "content: "
                + f"{json.dumps(json_str, ensure_ascii=False, indent=2)}\n")
            file.write('\n')

    # CLI Interface
    def main(self):
        parser = argparse.ArgumentParser(
            description="This LLM API client offers versatile "
                        + "options for generating text with LLM API."
                        + "You can provide a source as either a URL, "
                        + "a file path, or directly as a prompt.")

        parser.add_argument('sources',
                            nargs='*',
                            help="Specify the source for the prompt. "
                                 + "Can be a URL, a file path, "
                                 + "or a direct prompt text.")
        parser.add_argument('-i',
                            '--pdf-as-image',
                            action='store_true',
                            help="Read pdf as image.")
        args = parser.parse_args()

        if args.pdf_as_image is True:
            global PDF_AS_IMAGE
            PDF_AS_IMAGE = True

        if sys.stdin.isatty():
            if args.sources is None:
                self.talk(None)
            else:
                self.process_sources(args.sources)
        else:
            if args.sources is not None:
                msg = "Warning: In the case of pipe processing, "
                msg += "arguments excluding options will be ignored."
                print(msg)
            stdin_input = sys.stdin.read()
            message = f"{stdin_input}"
            data = self.append_to_data(None, message)
            self.send_and_print(data)
