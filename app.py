import os
import uuid
import streamlit as st

from rag_helper import (
    add_documents_to_database,
    answer_question,
    get_relevant_chunks,
    SUPPORTED_FILE_TYPES,
)


st.set_page_config(
    page_title="RAGDocs",
    page_icon="📚",
)

st.title("📚 RAGDocs")

st.write(
    "Ask questions about your PDF, Word, Excel, CSV, and Markdown files."
)

st.caption(
    "A small learning project using Streamlit, LangChain, Ollama, and ChromaDB."
)


# Session state

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "collection_name" not in st.session_state:
    st.session_state.collection_name = (
        "docs_" + uuid.uuid4().hex[:12]
    )

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []


# Sidebar

with st.sidebar:
    st.header("Model settings")

    ollama_url = st.text_input(
        "Ollama URL",
        value=os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        ),
    )

    chat_model_name = st.text_input(
        "Chat model",
        value=os.getenv(
            "OLLAMA_CHAT_MODEL",
            "gemma3:4b",
        ),
        help="The model that writes the answer.",
    )

    embedding_model_name = st.text_input(
        "Embedding model",
        value=os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "nomic-embed-text",
        ),
        help="The model that turns text into vectors for searching.",
    )

    st.subheader("Text splitting")

    chunk_size = st.number_input(
        "Chunk size",
        min_value=200,
        max_value=2000,
        value=800,
    )

    chunk_overlap = st.number_input(
        "Chunk overlap",
        min_value=0,
        max_value=500,
        value=100,
    )

    number_of_results = 5


# Add documents

st.header("1. Add documents")

st.write(
    "Choose files, then click the button to read and index them."
)

uploaded_files = st.file_uploader(
    "Select files",
    type=SUPPORTED_FILE_TYPES,
    accept_multiple_files=True,
)


if st.button(
    "Process files",
    type="primary",
    disabled=not uploaded_files,
):

    try:
        progress = st.progress(0)
        status_text = st.empty()

        def show_progress(
            current_file,
            total_files,
            file_name,
        ):
            progress.progress(
                current_file / total_files
            )
            status_text.write(
                f"Processing {file_name} "
                f"({current_file} of {total_files})"
            )

        new_files = [
            file
            for file in uploaded_files
            if file.name not in st.session_state.indexed_files
        ]

        if not new_files:
            st.info(
                "These files have already been processed in this session."
            )

        else:
            file_information = add_documents_to_database(
                files=new_files,
                ollama_url=ollama_url,
                embedding_model_name=embedding_model_name,
                chunk_size=int(chunk_size),
                chunk_overlap=int(chunk_overlap),
                collection_name=st.session_state.collection_name,
                progress_function=show_progress,
            )

            st.session_state.indexed_files.extend(
                file["name"]
                for file in file_information
            )

            total_chunks = sum(
                file["chunks"]
                for file in file_information
            )

            st.success(
                f"Added {len(file_information)} file(s) "
                f"and {total_chunks} text chunks."
            )

    except Exception as error:
        st.error(
            "There was a problem processing the files."
        )
        st.exception(error)


# Show indexed files

if st.session_state.indexed_files:

    st.subheader("Files in this session")

    for file_name in st.session_state.indexed_files:
        st.write("• " + file_name)


st.divider()

st.header("2. Ask a question")


if not st.session_state.indexed_files:
    st.info(
        "Process at least one file before asking a question."
    )


# Chat history

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.markdown(message["text"])


question = st.chat_input(
    "Ask something about your documents...",
    disabled=not st.session_state.indexed_files,
)


if question:

    st.session_state.chat_history.append({
        "role": "user",
        "text": question,
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        try:

            with st.spinner(
                "Searching the documents and writing an answer..."
            ):

                matching_chunks = get_relevant_chunks(
                    question=question,
                    ollama_url=ollama_url,
                    embedding_model_name=embedding_model_name,
                    collection_name=(
                        st.session_state.collection_name
                    ),
                    number_of_results=number_of_results,
                )

                answer = answer_question(
                    question=question,
                    matching_chunks=matching_chunks,
                    ollama_url=ollama_url,
                    chat_model_name=chat_model_name,
                )

            st.markdown(answer)

            st.session_state.chat_history.append({
                "role": "assistant",
                "text": answer,
            })

        except Exception as error:

            st.error(
                "I couldn't answer that question."
            )

            st.exception(error)

            st.session_state.chat_history.append({
                "role": "assistant",
                "text": "I couldn't answer that question.",
            })