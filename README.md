# RAGDocs — Local Multi-Document RAG Assistant

RAGDocs is a document question-answering application built with Python and Streamlit. Users can add several documents, ask questions about their contents, and inspect the passages used to produce an answer.

The application uses Retrieval-Augmented Generation (RAG): it searches the document collection for relevant text and gives that text to a language model as context. This helps connect answers to the uploaded documents instead of asking the model to answer from general knowledge alone.

## Supported documents

- PDF
- DOCX
- XLSX
- CSV
- Markdown (`.md` and `.markdown`)

The application extracts text from each file. Scanned PDFs contain images instead of selectable text and need OCR before they can be indexed.

## How it works

1. **Read:** Extract text from uploaded documents and keep basic source information, such as file name and page or sheet.
2. **Split:** Divide the extracted text into smaller overlapping chunks.
3. **Embed:** Use Ollama and `nomic-embed-text` to turn each chunk into a vector representation of its meaning.
4. **Store:** Save the chunks and vectors in a local ChromaDB collection.
5. **Retrieve:** Turn the user's question into a vector and search ChromaDB for similar chunks.
6. **Generate:** Send the question and retrieved text to the chat model, then display the answer with source passages.

```text
Uploaded documents → extracted text → chunks → embeddings → ChromaDB
                                                           ↓
Question → question embedding → relevant chunks → Gemma 3 4B → answer and sources
```

## Models

- **Chat model:** Gemma 3 4B (`gemma3:4b`), run locally with Ollama.
- **Embedding model:** `nomic-embed-text`, run locally with Ollama.

The chat model writes responses. The embedding model represents document chunks and questions as vectors so ChromaDB can find text with similar meaning. The model names and Ollama server address can be selected in the app's sidebar.

## Main features

- Upload multiple supported documents.
- Show progress while documents are being processed.
- Adjust chunk size and overlap to control how text is divided.
- Choose how many matching passages are retrieved for a question.
- Ask follow-up questions in a chat interface.
- Review the source text, file name, page or sheet, and similarity score for retrieved passages.
- Store vectors locally in ChromaDB and run both models through Ollama.

## Technology used

| Part | Technology |
| --- | --- |
| User interface | Streamlit |
| Application language | Python |
| Text splitting and model integrations | LangChain |
| Vector database | ChromaDB |
| Local model runtime | Ollama |
| Answer generation | Gemma 3 4B (`gemma3:4b`) |
| Text embeddings | `nomic-embed-text` |
| Document parsing | pypdf, python-docx, pandas, openpyxl |

## Project structure

- `app.py` contains the Streamlit page, upload and processing flow, model settings, and chat interface.
- `rag_helper.py` contains the document readers, chunking, embedding and ChromaDB search steps, and answer generation call.
- `requirements.txt` lists the Python packages used by the application.
- `chroma_db/` is created when the application runs and stores the local vector data.

## Answer grounding

The prompt tells the chat model to use the retrieved passages and to say when it cannot find an answer in them. RAG and source labels can make answers easier to check, but they do not guarantee that every answer is correct. Users should review the displayed passages when accuracy matters.

## Project summary

RAGDocs demonstrates a local RAG workflow for multi-document question answering: parsing different file types, splitting content into chunks, creating embeddings, storing and retrieving vectors, and generating answers with source context.
