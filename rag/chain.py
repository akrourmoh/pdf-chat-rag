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

How to answer:
- If CONTEXT is provided and the question is about the user's documents, answer using
  the CONTEXT. This INCLUDES summarising or describing what the document is about, or
  what type of document it is, based on the excerpts. Use any relevant information
  available in the CONTEXT, even if it is partial.
- Only reply "This information is not mentioned in the uploaded documents." when the
  question asks for a SPECIFIC detail that is clearly absent from the CONTEXT. Never
  use it for general or summary questions when CONTEXT is available.
- If no documents were provided, or the question is general or unrelated to the
  documents, answer normally using your own knowledge, like a normal AI assistant.

Other rules:
- LANGUAGE: Always write your answer in the SAME language as the user's question,
  regardless of the language of the CONTEXT or the documents. If the question is in
  French, answer in French; if it is in English, answer in English, and so on.
- Give complete, helpful answers; use Markdown when useful (**bold**, "## headings",
  "- bullets").
- Never invent specific facts about the documents that are not in the CONTEXT.
- If your answer is NOT based on the documents (general questions, greetings, small
  talk, or the "not mentioned" case), append the exact tag <no_sources> at the very end.

CONTEXT (from the user's documents):
{context}

Question: {question}

Answer:"""

    # Send the prompt to Gemini and return the generated answer
    return gemini_client.generate(prompt)
