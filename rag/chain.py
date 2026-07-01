import gemini_client  # shared Gemini client (handles the API + retries)


def get_answer(question, relevant_chunks):
    # This function takes the user's question and the relevant chunk records
    # retrieved from the PDF, and asks Gemini to generate an answer.

    # Join the text of all the relevant chunks into one block of context.
    # It may be empty if the user has not uploaded any documents.
    context = "\n\n".join(chunk["text"] for chunk in relevant_chunks)
    if not context.strip():
        context = "(no documents were provided)"

    # Build the prompt. The assistant is a general AI assistant that ALSO uses the
    # user's documents when relevant. It decides between three cases and marks any
    # reply not based on the documents so we can hide the sources line.
    prompt = f"""You are a helpful AI assistant, similar to ChatGPT or Claude. The user may have
uploaded documents; the relevant excerpts (if any) are provided below as CONTEXT.

Decide how to answer:
1. If the question is about the user's documents AND the answer is in the CONTEXT,
   answer using the CONTEXT.
2. If the question is clearly about the documents but the CONTEXT does not contain
   the answer, say clearly that this information is not mentioned in the uploaded
   documents.
3. If the question is general or unrelated to the documents (or no documents were
   provided), simply answer it normally using your own knowledge, like a normal AI
   assistant.

Other rules:
- Always answer in the same language as the question.
- Give complete, helpful answers; use Markdown when useful (**bold**, "## headings",
  "- bullets").
- Never invent facts about the documents that are not in the CONTEXT.
- If your answer is NOT taken from the documents (cases 2 and 3, greetings or small
  talk), append the exact tag <no_sources> on its own at the very end.

CONTEXT (from the user's documents):
{context}

Question: {question}

Answer:"""

    # Send the prompt to Gemini and return the generated answer
    return gemini_client.generate(prompt)
