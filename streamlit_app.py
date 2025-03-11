import streamlit as st
import google.generativeai as genai
import PyPDF2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize SentenceTransformer model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight transformer model

# PDF Loading function
def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ""
        return text
    except FileNotFoundError:
        st.error(f"PDF file not found.")
        return None
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

# Function to split the document into chunks based on paragraphs or headings
def split_text_into_chunks(text, chunk_size=1000):
    # Split the document by paragraphs or other logical delimiters
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk += "\n" + para
    
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# Function to get text embeddings
def get_text_embeddings(text_list):
    return model.encode(text_list)

# Function to search for the most relevant text chunk
def find_most_relevant_chunk(query, chunks):
    # Get the embedding of the user's query
    query_embedding = model.encode([query])[0]
    
    # Get embeddings of the document chunks
    chunk_embeddings = get_text_embeddings(chunks)
    
    # Calculate cosine similarity between query and document chunks
    similarities = cosine_similarity([query_embedding], chunk_embeddings)
    
    # Get the index of the most relevant chunk
    best_chunk_idx = np.argmax(similarities)
    
    # Return the most relevant chunk of text
    return chunks[best_chunk_idx]

# Streamlit App UI
st.title("Compliance Document Chatbot (Gemini 1.5 Flash)")

# Load PDF content (replace with your PDF file path)
PDF_FILE_PATH = "compliance_document.pdf"  # Replace with your PDF path
pdf_content = extract_text_from_pdf(PDF_FILE_PATH)

if pdf_content is None:
    st.stop()  # Stop execution if PDF loading failed

# Split the content into smaller chunks for semantic search
chunks = split_text_into_chunks(pdf_content)

# Prompt input field
prompt = st.text_input("Ask a question about the compliance document:", "")

# Button to generate response
if st.button("Generate Response"):
    if prompt:
        try:
            # Find the most relevant chunk based on the user's query
            relevant_chunk = find_most_relevant_chunk(prompt, chunks)
            
            if not relevant_chunk:
                st.write("No relevant content found for your question.")
            else:
                # Load and configure the model
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Create a combined prompt with the relevant content and user question
                combined_prompt = f"Here is the most relevant content from the compliance document:\n\n{relevant_chunk}\n\nUser Question: {prompt}\n\nAnswer the user's question based on the relevant content."

                # Generate response from the model
                response = model.generate_content(combined_prompt)

                # Display response in Streamlit
                st.write("Response:")
                st.write(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a prompt.")
