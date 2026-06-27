import gemini_client  # shared Gemini client (handles the API + retries)


def get_answer(question, relevant_chunks):
    # This function takes the user's question and the relevant chunk records
    # retrieved from the PDF, and asks Gemini to generate an answer.

    # Join the text of all the relevant chunks into one block of context
    context = "\n\n".join(chunk["text"] for chunk in relevant_chunks)

    # Build the prompt - we tell Gemini to answer using only the PDF content
    prompt = f"""You are a helpful assistant. Answer the question below using only the information provided in the context.
If the answer is not in the context, say "I don't know based on the uploaded documents."

Context (from the PDF):
{context}

Question: {question}

Answer:"""

    # Send the prompt to Gemini and return the generated answer
    return gemini_client.generate(prompt)
