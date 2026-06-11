import faiss        # FAISS - a library for fast similarity search on vectors
import numpy as np  # numpy - used to work with arrays of numbers


def build_vectorstore(embeddings):
    # This function takes a list of embeddings (vectors)
    # and stores them in a FAISS index so we can search them later

    # Convert the embeddings to a float32 numpy array (required by FAISS)
    vectors = np.array(embeddings).astype("float32")

    # Get the size (dimension) of one vector
    dimension = vectors.shape[1]

    # Create a FAISS index that uses simple L2 (euclidean) distance for similarity
    index = faiss.IndexFlatL2(dimension)

    # Add all our vectors into the index
    index.add(vectors)

    # Return the index
    return index


def search_vectorstore(index, query_embedding, chunks, top_k=4):
    # This function searches the FAISS index for the most similar chunks
    # to the user's question

    # Convert the query embedding to a float32 array and reshape it to 2D (required by FAISS)
    query_vector = np.array([query_embedding]).astype("float32")

    # Search the index - returns the distances and positions of the top_k closest vectors
    distances, indices = index.search(query_vector, top_k)

    # Use the positions (indices) to get the actual text chunks
    results = [chunks[i] for i in indices[0]]

    # Return the most relevant text chunks
    return results
