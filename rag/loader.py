import fitz  # PyMuPDF - the library that opens and reads PDF files


def load_pdfs(uploaded_files):
    # This function takes a list of PDF files uploaded by the user
    # and returns all their text combined into one big string

    # Start with an empty string - we will fill it as we read each PDF
    all_text = ""

    # Loop through each uploaded PDF file one by one
    for uploaded_file in uploaded_files:

        # Read the file as raw bytes (the file lives in memory, not on disk)
        pdf_bytes = uploaded_file.read()

        # Open the PDF from memory using PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Loop through every page inside this PDF
        for page in doc:

            # Extract the text from this page and add it to all_text
            all_text += page.get_text()

        # Close the PDF to free up memory when we are done with it
        doc.close()

    # Return all the text we collected from every page of every PDF
    return all_text
