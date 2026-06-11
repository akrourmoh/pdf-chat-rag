import streamlit as st              # Streamlit - builds our web UI
from rag.loader import load_pdfs        # our function to extract text from PDFs
from rag.chunker import split_text      # our function to split text into chunks
from rag.embedder import embed_chunks, embed_query  # our functions to convert text to vectors
from rag.vectorstore import build_vectorstore, search_vectorstore  # our vector database functions
from rag.chain import get_answer        # our function to ask Gemini for an answer


# ── Page configuration ──────────────────────────────────────────────────────
st.set_page_config(page_title="PDF Chat", page_icon="📄")
st.title("📄 Chat with your PDFs")


# ── Session state setup ──────────────────────────────────────────────────────
# Session state lets us remember things between user interactions (like a global variable)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (question, answer) pairs

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None  # the FAISS index (empty until PDFs are processed)

if "chunks" not in st.session_state:
    st.session_state.chunks = []  # the list of text chunks from the PDFs


# ── Sidebar - PDF upload ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload your PDFs")

    # File uploader - allows multiple PDF files
    uploaded_files = st.file_uploader(
        "Choose one or more PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    # Button to start processing the uploaded PDFs
    if st.button("Process PDFs"):

        # Make sure the user actually uploaded something
        if not uploaded_files:
            st.warning("Please upload at least one PDF file.")
        else:
            # Show a spinner while we process the PDFs
            with st.spinner("Reading and processing your PDFs..."):

                # Step 1: Extract all text from the uploaded PDFs
                raw_text = load_pdfs(uploaded_files)

                # Step 2: Split the text into smaller chunks
                chunks = split_text(raw_text)

                # Step 3: Convert the chunks into vectors (embeddings)
                embeddings = embed_chunks(chunks)

                # Step 4: Store the vectors in a FAISS index
                vectorstore = build_vectorstore(embeddings)

                # Save the chunks and vectorstore in session state so we can use them later
                st.session_state.chunks = chunks
                st.session_state.vectorstore = vectorstore

            # Show a success message when done
            st.success(f"Done! {len(chunks)} chunks stored from {len(uploaded_files)} file(s).")


# ── Main area - Chat interface ───────────────────────────────────────────────

# Display all previous messages in the chat
for question, answer in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.write(answer)

# Input box at the bottom for the user to type a question
user_question = st.chat_input("Ask a question about your PDFs...")

if user_question:
    # Make sure PDFs have been processed before allowing questions
    if st.session_state.vectorstore is None:
        st.warning("Please upload and process your PDFs first.")
    else:
        # Show the user's question in the chat
        with st.chat_message("user"):
            st.write(user_question)

        # Generate the answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                # Step 1: Convert the question into a vector
                query_embedding = embed_query(user_question)

                # Step 2: Find the most relevant chunks from the PDFs
                relevant_chunks = search_vectorstore(
                    st.session_state.vectorstore,
                    query_embedding,
                    st.session_state.chunks
                )

                # Step 3: Ask Gemini to answer using those chunks
                answer = get_answer(user_question, relevant_chunks)

            # Display the answer
            st.write(answer)

        # Save this question and answer to the chat history
        st.session_state.chat_history.append((user_question, answer))
