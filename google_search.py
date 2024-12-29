import argparse
import json
import os
import requests
import urllib.parse

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus \
        import focus_next, focus_previous
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings \
        import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.shortcuts import dialogs, prompt
from prompt_toolkit.widgets import Button, Dialog, Label, RadioList
from rich.console import Console
from rich.rule import Rule


API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY is None:
    print("GOOGLE_API_KEY environment variable must be set.")
    exit(1)
CSE_ID = os.getenv("GOOGLE_CSE_ID", None)
if CSE_ID is None:
    print("GOOGLE_CSE_ID environment variable must be set.")
    exit(1)
HELPER_CLASS = os.getenv("SEARCH_HELPER")
if HELPER_CLASS is None:
    print("SEARCH_HELPER environment variable must be set.")
    exit(1)

if HELPER_CLASS == "openai":
    import openai
    search_helper = openai.OPENAI(os.getenv("OPENAI_MODEL"))
else:
    import gemini
    search_helper = gemini.Gemini(os.getenv("GEMINI_MODEL"))

# rich
console = Console()
separator = Rule(style='bold yellow')

def select_list(title, explanation, items, default):

    if items is None:
        items = []

    radio_list = RadioList(values=items, default=default)

    def ok_handler() -> None:
        get_app().exit(result=radio_list.current_value)

    dialog = Dialog(
        title=title,
        body=HSplit(
            [Label(text=explanation), radio_list],
            padding=1,
        ),
        buttons=[
            Button(text="OK", handler=ok_handler),
            Button(text="Cancel", handler=dialogs._return_none),
        ],
        with_background=True,
    )

    bindings = KeyBindings()
    bindings.add("right")(focus_next)
    bindings.add("left")(focus_previous)
    bindings.add("c-d")(lambda event: event.app.exit())
    bindings.add("c-delete")(lambda event: event.app.exit())

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
        mouse_support=True,
        style=None,
        full_screen=True,
    ).run()


def search(query):

    param = {
        "q": query
    }
    encoded = urllib.parse.urlencode(param)

    base_url = "https://www.googleapis.com/customsearch/v1?" \
        + f"key={API_KEY}&cx={CSE_ID}&{encoded}"

    headers = {}

    startIndex = 0

    while True:

        url = base_url + f"&start={startIndex}"
        response = requests.get(url, headers=headers, timeout=(10.0, 10.0))

        search_results = {}
        if response.status_code == 200:
            response.encoding = 'utf-8'
            search_results = response.json()
        else:
            json_str = json.dumps(response.json(), ensure_ascii=False, indent=2)
            print(f"Failed to retrieve the web page: {url}")
            print(f"Response: {json_str}")
            return False

        if 'items' not in search_results:
            print("No results.")
            return False

        links = []

        for item in search_results['items']:
            links.append((item['link'], item['title']))

        prevIndex = -1
        nextIndex = -1

        if 'queries' in search_results:
            if 'previousPage' in search_results['queries']:
                prevIndex =\
                    search_results['queries']['previousPage'][0]['startIndex']
                links.append(('Previous', 'Previous'))
            if 'nextPage' in search_results['queries']:
                nextIndex =\
                    search_results['queries']['nextPage'][0]['startIndex']
                links.append(('Next', 'Next'))

        result = None

        while True:

            result = select_list(
                    'Search Results',
                    f'{query}',
                    links, result)

            if result is None:
                return True

            if result == 'Previous':
                startIndex = prevIndex
                break

            if result == 'Next':
                startIndex = nextIndex
                break

            selected_title = next((title for url,
                                   title in links if url == result), None)
            console.print(separator)
            console.print(selected_title)
            console.print(result)
            search_helper.clear()
            if search_helper.process_sources([result]) is False:
                prompt("Press the enter key to continue. ")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="Web search utility")

    parser.add_argument('query',
                        nargs='*',
                        help="Specify query keywords.")

    args = parser.parse_args()

    if len(args.query) == 0:
        print('Query string is not specified.')
    else:
        search(' '.join(args.query))
