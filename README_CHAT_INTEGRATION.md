Chat — Jupyter integration

Quick start

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Set your API key (example on Windows PowerShell):

```powershell
$env:OPENAI_API_KEY = "sk-..."
# Optionally:
$env:OPENAI_CHAT_MODEL = "gpt-4o-mini"
```

3. Open `chat_integration.ipynb` in JupyterLab/Notebook and run cells. Use the text area + Send button to chat.

Notes

- The notebook uses the `openai` Python client and a simple `ipywidgets` UI. Adjust the `MODEL` via `OPENAI_CHAT_MODEL` environment variable.
- The Save button writes the conversation to `jupyter_chat_history.txt` in the notebook folder.
- If you prefer a different API endpoint, replace the `chat_call` function implementation accordingly.

Security

- Do not commit your API key to source control. Use environment variables or a secrets manager.
