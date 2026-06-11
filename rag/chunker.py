from langchain_text_splitters import RecursiveCharacterTextSplitter
# RecursiveCharacterTextSplitter is a LangChain tool that splits long text into smaller pieces


def split_text(text):
    # This function takes a long string of text (from our PDFs)
    # and splits it into smaller chunks so the AI can process it more easily

    # Create the splitter with our settings
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,    # each chunk will have at most 1000 characters
        chunk_overlap=200   # the last 200 characters of one chunk are repeated at the start of the next
                            # this overlap helps avoid losing meaning at the edges of chunks
    )

    # Split the text into a list of chunks
    chunks = splitter.split_text(text)

    # Return the list of chunks
    return chunks
