import os                      # os - used to read environment variables
from google import genai       # Google's current (supported) Gemini SDK
from dotenv import load_dotenv  # load_dotenv reads our .env file to get the API key

# Load the API key from the .env file and create a Gemini client.
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# The Gemini chat model we use to generate answers.
LLM_MODEL = "gemini-2.5-flash"


def get_answer(question, relevant_chunks):
    # This function takes the user's question and the relevant text chunks
    # retrieved from the PDF, and asks Gemini to generate an answer.

    # Join all the relevant chunks into one block of context text
    context = "\n\n".join(relevant_chunks)

    # Build the prompt - we tell Gemini to answer using only the PDF content
    prompt = f"""You are a helpful assistant. Answer the question below using only the information provided in the context.
If the answer is not in the context, say "I don't know based on the uploaded documents."

Context (from the PDF):
{context}

Question: {question}

Answer:"""

    # Send the prompt to Gemini and get the response
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
    )

    # Return the text of the response
    return response.text
