# RAGDocs

RAGDocs is a small document question-answering app made with Streamlit. It is also a learning project for understanding RAG, embeddings, and vector databases.

## What happens when I ask a question?

1. The app reads text from the uploaded files.
2. It splits the text into smaller chunks.
3. Ollama turns each chunk into an embedding (a list of numbers that represents the text).
4. ChromaDB saves the chunks and embeddings in a local folder.
5. When you ask a question, the app searches for chunks with similar embeddings.
6. The chat model gets those chunks and writes an answer with source labels.

The answer model is told to use the retrieved text only. This can reduce made-up answers, but cannot guarantee that the model is always correct. Check the source passages for important information.

## Supported files

- PDF
- DOCX
- XLSX
- CSV
- Markdown (`.md` and `.markdown`)

Scanned PDFs are pictures and do not contain selectable text. Run OCR on those files before uploading them.

## Install and run on your computer

You need Python 3.10 or newer and [Ollama](https://ollama.com/download).

Pull the two default models in a terminal:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Create a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell, activate it, install the packages, and run Streamlit:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

On macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit, usually `http://localhost:8501`.

## Change the models

The sidebar has fields for the Ollama URL, chat model, and embedding model. The defaults are:

- Ollama URL: `http://localhost:11434`
- Chat model: `llama3.2`
- Embedding model: `nomic-embed-text`

You can enter other model names if they are installed in Ollama. Use the same embedding model for the files in one session.

Environment variables can set the default values. For example, in PowerShell:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_CHAT_MODEL = "llama3.2"
$env:OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
streamlit run app.py
```

## How the code is organized

- `app.py` contains the page, file upload, progress message, settings, and chat.
- `rag_helper.py` contains file reading, chunking, vector search, and model calls.
- `requirements.txt` lists the Python packages used by the app.
- `chroma_db/` is created when you run the app and stores vectors. It is excluded from Git.

## Deployment

You can put this code on GitHub and deploy the Streamlit app from that repository. A hosted Streamlit app cannot use `localhost` to reach Ollama on your personal computer. For cloud deployment, configure an Ollama server that the hosted app can reach. Protect that server; do not expose an unauthenticated Ollama endpoint to the public internet.

Some free hosting services remove local files when they restart. This app saves Chroma data in `chroma_db`, so use a host with persistent storage if you need to keep the index after a restart.

## Put the project on GitHub

First create an empty repository on GitHub. Then run these commands in this folder and replace the URL with your repository URL:

```bash
git init
git add .
git commit -m "Add beginner RAGDocs app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ragdocs.git
git push -u origin main
```

Do not add private documents, the `chroma_db` folder, or secrets to GitHub.
