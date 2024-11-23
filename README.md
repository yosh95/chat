# LLM Chat Client with Web Search Integration

This project provides a command-line interface (CLI) chat client that interacts with various Large Language Models (LLMs) and integrates with Google Custom Search to enhance the conversation experience.  It supports OpenAI and Google Gemini APIs.

## Features

* **Multi-LLM Support:**  Currently supports OpenAI and Google Gemini APIs.  Switching between models is done by setting environment variables.
* **File and URL Input:**  Allows providing input from various sources, including local files (text, PDF, images), and URLs.  PDFs can be processed as text or images (depending on settings).
* **Interactive Chat:**  Provides a conversational interface for interacting with the chosen LLM.
* **Conversation History:**  Maintains and displays a history of the conversation.
* **Command-line Controls:**  Offers commands to clear the conversation history, view information about the session, quit, and open URLs in a web browser.
* **Google Custom Search Integration:** Integrates with Google Custom Search to allow for context-aware web searches during the chat session. This helps the LLM access relevant external information.
* **Grounding (Gemini only):**  The Gemini integration allows the use of grounding, enabling the model to retrieve information from Google Search to answer your queries more accurately.  This is optional and controlled by an environment variable or command-line option.
* **Request Logging:** Logs requests and responses to a file for debugging purposes.  This helps troubleshoot issues with API calls.

## Requirements

Install the necessary packages using pip:

```bash
pip install -r requirements.txt
```

## Setup

1. **API Keys:** Obtain API keys for OpenAI and/or Google Gemini.

2. **Environment Variables:** Set the following environment variables (replace with your actual keys and settings):

   Or create a `.env` file in the project root directory and add the following API keys and settings:

   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   export OPENAI_MODEL="gpt-3.5-turbo"  # or another suitable OpenAI model
   export GEMINI_API_KEY="your_gemini_api_key"
   export GEMINI_MODEL="models/text-bison-001" # or another suitable Gemini model
   export GOOGLE_API_KEY="your_google_custom_search_api_key"
   export GOOGLE_CSE_ID="your_google_custom_search_engine_id"
   export SEARCH_HELPER="openai" # or "gemini"
   export PROMPT_HISTORY="$HOME/.chat_prompt_history"
   export REQUEST_DEBUG_LOG="$HOME/.chat_request_debug_log"
   ```

3. **Run:** Execute the main script (you'll likely want to run `google_search.py`):

   ```bash
   python3 google_search.py "your search query"
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

To add support for another LLM, create a new Python file (e.g., `new_llm.py`) and create a class that inherits from `chat.Chat`.  Implement the `_send()` method to handle sending requests and receiving responses from the new LLM's API.  Update the `.env` file with the necessary API keys and model names.


## Contributing

Contributions are welcome!  Please open an issue or submit a pull request if you have any suggestions or improvements.


## License

MIT license

