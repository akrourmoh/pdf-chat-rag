from langchain_text_splitters import RecursiveCharacterTextSplitter
# RecursiveCharacterTextSplitter is a LangChain tool that splits long text into smaller pieces

import config  # central settings (chunk size, overlap, etc.)


def split_documents(pages):
    # This function takes the list of page records from the loader and splits
    # each page's text into smaller chunks. Crucially, it copies the page's
    # source/page metadata onto EVERY chunk, so each chunk still knows where it
    # came from after splitting.

    # Create the splitter with our settings (read from the central config)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,       # max characters per chunk
        chunk_overlap=config.CHUNK_OVERLAP  # characters shared between consecutive chunks
                                            # (helps avoid losing meaning at chunk edges)
    )

    # Build the final list of chunk records
    chunks = []
    for page in pages:
        for piece in splitter.split_text(page["text"]):
            chunks.append({
                "text": piece,             # the chunk's text
                "source": page["source"],  # carried over from the page
                "page": page["page"],      # carried over from the page
            })

    # Return the list of chunk records
    return chunks
