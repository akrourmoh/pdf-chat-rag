import os                          # os - used to read environment variables
import google.generativeai as genai # Google's library to talk to the Gemini API
from dotenv import load_dotenv      # load_dotenv reads our .env file to get the API key

# Load the API key from the .env file
load_dotenv()

# Configure the Gemini API with our key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the Gemini 2.5 Flash model
llm = genai.GenerativeModel("gemini-2.5-flash")


def get_answer(question, relevant_chunks):
    # This function takes the user's question and the relevant text chunks
    # retrieved from the PDF, and asks Gemini to generate an answer

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
    response = llm.generate_content(prompt)

    # Return the text of the response
    return response.text
