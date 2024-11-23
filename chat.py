#!/usr/bin/env python3

import argparse
import base64
import filetype
import json
import os
import re
import requests
import sys
import webbrowser

from bs4 import BeautifulSoup
from collections import deque
from io import BytesIO
from prompt_toolkit.history import FileHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import prompt
from pypdf import PdfReader

# Constants
INPUT_HISTORY = os.getenv("CHAT_PROMPT_HISTORY", None)
REQUEST_DEBUG_LOG = os.getenv("CHAT_REQUEST_DEBUG_LOG", None)
PDF_AS_IMAGE = False

# prompt_toolkit
kb = KeyBindings()


class Chat():

    MODEL = ""

    chat_history_file = None

    last_usage = None

    grounding = False

    grounding_results = None

    stdout = False

    conversation = deque()

    def __init__(self, model):
        self.MODEL = model

    @kb.add('c-delete')
    def _(event):
        raise KeyboardInterrupt

    @kb.add('c-j')
    def _(event):
        event.current_buffer.insert_text('\n')

    def clear(self):
        self.last_usage = None
        self.grounding_results = None
        self.conversation.clear()

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

    def calc_data_size(self, data):
        sum = 0
        if data is None:
            return 0
        for i in data:
            sum += len(i['content'])
        return sum

    def send_and_print(self, data):
        response, self.last_usage, self.grounding_results = \
            self._send(data, self.conversation)
        print(f"({self.MODEL}):\n{response}")

    def talk(self, data, sources=None):

        if data is None:
            data = []

        data_size = self.calc_data_size(data)

        if INPUT_HISTORY is None:
            prompt_history = InMemoryHistory()
        else:
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
                if user_input != '':
                    print("----")
                user_input = user_input.strip()
            except UnicodeDecodeError as e:
                print(e)
                continue
            except KeyboardInterrupt:
                break
            except EOFError:
                break

            # special commands
            if user_input in ['.c', '.clear']:
                self.conversation.clear()
                print("Conversation history has been cleared.")
                continue
            if user_input in ['.h', '.hist', '.history']:
                print(json.dumps(list(self.conversation),
                                 indent=2, ensure_ascii=False))
                continue
            if user_input in ['.i', '.info']:
                print(f"model: {self.MODEL}")
                print(f"sources: {sources}")
                print(f"passed data size: {data_size}")
                print(f"last usage: ", end="")
                print(json.dumps(self.last_usage,
                                 indent=2, ensure_ascii=False))
                print(f"grounding: {self.grounding}")
                print(f"grounding results: ", end="")
                print(json.dumps(self.grounding_results,
                                 indent=2, ensure_ascii=False))
                continue
            if user_input in ['.q', '.quit']:
                break
            if user_input in ['.o', '.open']:
                if sources is not None and len(sources) > 0:
                    url = sources[0]
                    match = re.match(r"^(https?://)", url)
                    if match:
                        print(f"{url}")
                        webbrowser.open(sources[0])
                    else:
                        print("Only URLs starting with http:// or https:// "
                              + "can be processed.")
                else:
                    print("URL is not specified as an argument.")
                continue
            if user_input in ['.g', '.grounding']:
                if self.grounding is True:
                    self.grounding = False
                    print("Grounding is set to False.")
                else:
                    self.grounding = True
                    print("Grounding is set to True.")
                continue
            if user_input == '':
                continue
            else:
                data = self.append_to_data(data, user_input)
                self.send_and_print(data)
            data = []

        if self.chat_history_file is not None:
            self.deque_to_json(self.conversation, self.chat_history_file)

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
        try:
            response = requests.get(url,
                                    headers=headers,
                                    timeout=(10.0, 10.0))
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
        direct_prompt = True
        for source in sources:
            if source.startswith("http"):
                content, content_type = self.fetch_url_content(source)
                direct_prompt = False
            elif os.path.exists(source):
                content_type = None
                kind = filetype.guess(source)
                if kind and kind.extension == 'pdf':
                    if PDF_AS_IMAGE is True:
                        content = self.encode_data_from_file(source)
                        content_type = "application/pdf"
                    else:
                        content = self.read_pdf_from_file(source)
                        content_type = "text/plain"
                elif kind and 'image/' in kind.mime:
                    content = self.encode_data_from_file(source)
                    content_type = kind.mime
                else:
                    content = self.read_text_from_file(source)
                direct_prompt = False
            else:
                content = source
                content_type = "text/plain"

            if content is not None:
                data.append({
                    "content": content,
                    "content_type": content_type
                })

        if direct_prompt is True:
            self.send_and_print(data)
            if self.stdout is False:
                self.talk(None, sources=sources)
        else:
            if self.stdout is False:
                self.talk(data, sources=sources)
            else:
                self.send_and_print(data)

    def write_request_debug_log(self, headers, data, response):
        if REQUEST_DEBUG_LOG is None:
            return

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

    def deque_to_json(self, deque_obj, filepath):
        try:
            with open(filepath, 'w+', encoding='utf-8') as f:
                json.dump(list(deque_obj), f, indent=2, ensure_ascii=False)
        except (IOError, TypeError) as e:
            print(f"Error: Failed to save json. {e}")

    def json_to_deque(self, filepath):
        if os.path.isfile(filepath) is False:
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return deque(data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            print(f"Error: Failed to load json. {e}")
            return None

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
        parser.add_argument('--hist',
                            '--history-file',
                            help="Chat history file.")
        parser.add_argument('-i',
                            '--pdf-as-image',
                            action='store_true',
                            help="Read pdf as image.")
        parser.add_argument('-g',
                            '--grounding',
                            action='store_true',
                            help="Use grounding.")
        parser.add_argument('-s',
                            '--stdout',
                            action='store_true',
                            help="Redirect the output to STDOUT.")
        args = parser.parse_args()

        if args.pdf_as_image is True:
            global PDF_AS_IMAGE
            PDF_AS_IMAGE = True

        self.grounding = args.grounding

        self.stdout = args.stdout

        if args.hist is not None:
            self.chat_history_file = args.hist
            hist = self.json_to_deque(self.chat_history_file)
            if hist is not None:
                self.conversation = hist

        if sys.stdin.isatty():
            if args.sources is None or len(args.sources) == 0:
                self.talk(None)
            else:
                self.process_sources(args.sources)
        else:
            stdin_input = sys.stdin.read()
            message = f"{stdin_input}"
            data = self.append_to_data(None, message)
            self.send_and_print(data)
