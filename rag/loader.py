import fitz  # PyMuPDF - the library that opens and reads PDF files


def load_pdfs(files):
    # This function takes a list of (filename, pdf_bytes) pairs and returns a
    # list of "page records". Each record keeps the page's text together with
    # WHERE it came from (the file name and the page number), so later we can
    # tell the user which document and page an answer is based on.

    # Start with an empty list - we will add one record per page
    pages = []

    # Loop through each (name, bytes) pair
    for source, pdf_bytes in files:

        # Open the PDF from memory using PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Loop through every page; enumerate(start=1) gives human-friendly page numbers
        for page_number, page in enumerate(doc, start=1):

            # Extract the text from this page
            text = page.get_text()

            # Skip blank pages (e.g. scanned images with no extractable text)
            if text.strip():
                pages.append({
                    "source": source,      # which file this came from
                    "page": page_number,   # which page (1-based)
                    "text": text,          # the page's text
                })

        # Close the PDF to free up memory when we are done with it
        doc.close()

    # Return all the page records we collected
    return pages
