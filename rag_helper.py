import hashlib
import io
from pathlib import Path

import pandas as pd
from docx import Document as WordDocument
from pypdf import PdfReader

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_FILE_TYPES = ["pdf", "docx", "xlsx", "csv", "md", "markdown"]
CHROMA_FOLDER = Path(__file__).parent / "chroma_db"
BATCH_SIZE = 16


def read_file(uploaded_file):
    """Read the uploaded file."""

    name = uploaded_file.name
    ext = Path(name).suffix.lower()
    data = uploaded_file.getvalue()
    documents = []
    sections = 0

    if ext == ".pdf":
        pdf = PdfReader(io.BytesIO(data))
        sections = len(pdf.pages)

        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""

            if text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "name": name,
                            "location": f"Page {page_no}",
                        },
                    )
                )

    elif ext == ".docx":
        doc = WordDocument(io.BytesIO(data))
        text = [p.text for p in doc.paragraphs if p.text.strip()]

        for table in doc.tables:
            for row in table.rows:
                text.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        sections = len(doc.paragraphs) + len(doc.tables)

        if text:
            documents.append(
                Document(
                    page_content="\n".join(text),
                    metadata={
                        "name": name,
                        "location": "Word document",
                    },
                )
            )

    elif ext == ".xlsx":
        sheets = pd.read_excel(
            io.BytesIO(data),
            sheet_name=None,
            dtype=str,
        )

        sections = len(sheets)

        for sheet_name, table in sheets.items():
            table = table.fillna("")

            documents.append(
                Document(
                    page_content=(
                        f"Sheet: {sheet_name}\n"
                        f"{table.to_csv(index=False)}"
                    ),
                    metadata={
                        "name": name,
                        "location": f"Sheet: {sheet_name}",
                    },
                )
            )

    elif ext == ".csv":
        table = pd.read_csv(
            io.BytesIO(data),
            dtype=str,
            keep_default_na=False,
        )

        sections = len(table)

        documents.append(
            Document(
                page_content=table.to_csv(index=False),
                metadata={
                    "name": name,
                    "location": "CSV file",
                },
            )
        )

    elif ext in [".md", ".markdown"]:
        documents.append(
            Document(
                page_content=data.decode(
                    "utf-8-sig",
                    errors="replace",
                ),
                metadata={
                    "name": name,
                    "location": "Markdown file",
                },
            )
        )
        sections = 1

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    if not any(d.page_content.strip() for d in documents):
        raise ValueError(
            f"No text found in {name}. "
            "A scanned PDF needs OCR first."
        )

    return documents, sections


def make_vector_database(
    ollama_url,
    embedding_model,
    collection_name,
):
    embeddings = OllamaEmbeddings(
        model=embedding_model,
        base_url=ollama_url.rstrip("/"),
        keep_alive=0,
    )

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_FOLDER),
    )


def add_documents_to_database(
    files,
    ollama_url,
    embedding_model_name,
    chunk_size,
    chunk_overlap,
    collection_name,
    progress_function=None,
):
    """Read, split and store documents."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    db = make_vector_database(
        ollama_url,
        embedding_model_name,
        collection_name,
    )

    file_information = []

    for file_no, file in enumerate(files, 1):
        documents, sections = read_file(file)
        chunks = splitter.split_documents(documents)

        if not chunks:
            raise ValueError(f"No chunks created for {file.name}")

        file_hash = hashlib.sha256(
            file.getvalue()
        ).hexdigest()

        ids = []

        for i, chunk in enumerate(chunks):
            text = f"{file_hash}-{i}-{chunk.page_content}"
            ids.append(
                hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest()
            )

        for i in range(0, len(chunks), BATCH_SIZE):
            db.add_documents(
                chunks[i:i + BATCH_SIZE],
                ids=ids[i:i + BATCH_SIZE],
            )

        file_information.append({
            "name": file.name,
            "sections": sections,
            "chunks": len(chunks),
        })

        if progress_function:
            progress_function(
                file_no,
                len(files),
                file.name,
            )

    return file_information


def get_relevant_chunks(
    question,
    ollama_url,
    embedding_model_name,
    collection_name,
    number_of_results=5,
):
    """Get the five most relevant chunks."""

    db = make_vector_database(
        ollama_url,
        embedding_model_name,
        collection_name,
    )

    results = db.similarity_search(
        question,
        k=5,
    )

    return [doc.page_content for doc in results]


def answer_question(
    question,
    matching_chunks,
    ollama_url,
    chat_model_name,
):
    """Use the retrieved chunks to answer the question."""

    if not matching_chunks:
        return "I could not find enough information in the documents."

    context = "\n\n---\n\n".join(matching_chunks)

    prompt = f"""
Answer the question using the information from the documents below.

Use all the relevant information and combine it into one clear,
complete and detailed answer.

Do not mention sources, pages, files, chunks or the retrieval process.
Do not make up information that is not supported by the documents.

Give only the final answer.

Documents:
{context}

Question:
{question}

Answer:
"""

    model = ChatOllama(
        model=chat_model_name,
        base_url=ollama_url.rstrip("/"),
        temperature=0.1,
        num_ctx=3072,
        num_predict=700,
        keep_alive=0,
    )

    response = model.invoke(prompt)
    return str(response.content)