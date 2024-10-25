# LLM Chat Tool

This repository contains a command-line tool for interacting with Large Language Models (LLMs) like
Google Gemini and OpenAI.  It allows you to have conversations, provide prompts from various sources
 (URLs, files, or direct input), and manage conversation history. It also includes a web search util
ity to augment your prompts with information from Google Custom Search.

## Features

* **Multi-LLM Support:** Currently supports Google Gemini and OpenAI.  Easily extensible to other LL
Ms.
* **Versatile Input:**  Accept prompts from direct input, files (text, PDF, images), and URLs (web p
ages, PDFs, images).
* **Conversation History:**  Maintain and manage conversation history for context-rich interactions.

* **Special Commands:** Clear history, view history, display information, and quit the application.
* **Web Search Integration:** Search the web using Google Custom Search and directly use search resu
lts as input for the LLM.
* **Interactive Prompting:**  Uses `prompt_toolkit` for a user-friendly command-line experience with
 features like history, auto-completion, and keyboard shortcuts.
* **PDF Handling:** Extracts text from PDFs for use in prompts. Optionally treat PDFs as images.
* **Image Support:**  Encode images as base64 for use with compatible LLMs (e.g., OpenAI).
* **Request Debugging:**  Logs request and response details for troubleshooting.


## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yosh95/chat.git
   cd chat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root directory and add the following API keys and settings:

   ```
   OPENAI_API_KEY=<your_openai_api_key>
   OPENAI_MODEL=<your_openai_model_name>  # e.g., gpt-3.5-turbo, gpt-4

   GEMINI_API_KEY=<your_gemini_api_key>
   GEMINI_MODEL=<your_gemini_model_name> # e.g., chat-bison-001

   GOOGLE_API_KEY=<your_google_custom_search_api_key>
   GOOGLE_CSE_ID=<your_google_custom_search_engine_id>

   SEARCH_HELPER=openai  # or gemini, depending on which LLM you want to use for search assistance.
   ```

## Usage

**Basic Chat:**

```bash
python <LLM_script>.py  # e.g., python gemini.py or python openai.py
```
This starts an interactive chat session with the specified LLM.  Type your prompt and press Enter.

**Input from File or URL:**

```bash
python <LLM_script>.py <file_path_or_url>
python <LLM_script>.py "This is a direct prompt."
python <LLM_script>.py https://www.example.com/page.html /path/to/file.txt
```
This sends the content of the file or URL as a prompt to the LLM. You can specify multiple files or
URLs.

**PDF as Image:**

```bash
python <LLM_script>.py --pdf-as-image <pdf_file_path>
```

or

```bash
python <LLM_script>.py -i <pdf_file_path>
```

This sends the PDF as an image to the LLM instead of extracting text.

**Web Search:**

```bash
python search.py <search_query>
```
This performs a Google Custom Search and lets you select a result to send as a prompt to the search
helper LLM.


**In-Chat Commands:**

* `.c` or `.clear`: Clear the conversation history.
* `.h` or `.hist` or `.history`: Display the conversation history.
* `.i` or `.info`: Display information about the current session (model, sources, etc.).
* `.q` or `.quit`: Quit the chat session.
* `.o` or `.open`: Open the first URL specified in the initial arguments in a web browser.

**Keyboard Shortcuts (using `prompt_toolkit`):**

* `Ctrl+Delete`: Exit the application.
* `Ctrl+J`: Insert a newline character.


## Extending to Other LLMs

To add support for another LLM, create a new Python file (e.g., `new_llm.py`) and create a class tha
t inherits from `chat.Chat`.  Implement the `_send()` method to handle sending requests and receivin
g responses from the new LLM's API.  Update the `.env` file with the necessary API keys and model na
mes.


## Contributing

Contributions are welcome!  Please open an issue or submit a pull request if you have any suggestion
s or improvements.


## License

This project is licensed under the MIT License.  See the [LICENSE](LICENSE) file for details.

