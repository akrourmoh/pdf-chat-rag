import gemini_client  # shared Gemini client (handles the API + retries)


def get_answer(question, relevant_chunks):
    # This function takes the user's question and the relevant chunk records
    # retrieved from the PDF, and asks Gemini to generate an answer.

    # Join the text of all the relevant chunks into one block of context
    context = "\n\n".join(chunk["text"] for chunk in relevant_chunks)

    # Build the prompt. We tell Gemini to answer ONLY from the context, but also
    # to give a complete, well-structured answer (not a bare yes/no) and to use
    # Markdown formatting so the frontend can render headings, bold and lists.
    prompt = f"""You are a helpful assistant answering questions about the user's documents.
Use ONLY the information in the context below. If the answer is not in the context,
say "I don't know based on the uploaded documents."

How to answer:
- Give a complete, helpful answer. Include the relevant specific details from the
  context - never reply with just "yes" or "no" when details are available.
- Format the answer in Markdown: use **bold** for key terms, short `##` headings
  when the answer has sections, and bullet points ("- ") for lists.
- Be clear and well-organized, but do not invent anything that is not in the context.

Context (from the documents):
{context}

Question: {question}

Answer:"""

    # Send the prompt to Gemini and return the generated answer
    return gemini_client.generate(prompt)
