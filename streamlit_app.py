import streamlit as st
import google.generativeai as genai
import PyPDF2
from bs4 import BeautifulSoup
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

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

# HTML Parsing function
def parse_html_content(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Extract text from the HTML content
        text = soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        st.error(f"Error parsing HTML: {e}")
        return None

# Function to split the document into chunks based on paragraphs or headings
def split_text_into_chunks(text, chunk_size=1000):
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

# Function to get text embeddings using TF-IDF
def get_text_embeddings(text_list):
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(text_list)
    return embeddings

# Function to search for the most relevant text chunk
def find_most_relevant_chunk(query, chunks):
    chunk_embeddings = get_text_embeddings(chunks)
    query_embeddings = get_text_embeddings([query])

    # Reshape the query embeddings to match the dimensions of the chunk embeddings
    query_embeddings = query_embeddings.reshape(1, -1)  # Ensure it's a 2D array (1, n_features)
    
    similarities = cosine_similarity(query_embeddings, chunk_embeddings)
    
    best_chunk_idx = np.argmax(similarities)
    
    return chunks[best_chunk_idx]

# Streamlit App UI
st.title("Mutual Fund Marketing Campaign Compliance Checker")

# Path to the pre-existing Compliance PDF Document
PDF_FILE_PATH = "compliance_document.pdf"  # Replace with the correct path to your compliance document
pdf_content = extract_text_from_pdf(PDF_FILE_PATH)

if pdf_content is None:
    st.stop()  # Stop execution if PDF loading failed

# Split the content into smaller chunks for semantic search
chunks = split_text_into_chunks(pdf_content)

# Upload HTML Content (Email or Creative)
html_file = st.file_uploader("Upload HTML Email/Creative", type="html")
if html_file is not None:
    html_content = html_file.read().decode("utf-8")
    parsed_html = parse_html_content(html_content)
    
    if parsed_html is None:
        st.stop()  # Stop execution if HTML parsing failed
    
    # Check compliance for the uploaded HTML content
    relevant_chunk = find_most_relevant_chunk(parsed_html, chunks)
    
    if relevant_chunk:
        # Load and configure the Generative AI Model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Create a combined prompt with the relevant content and HTML creative
        combined_prompt = f"Here is the most relevant content from the compliance document:\n\n{relevant_chunk}\n\nUser's Marketing Campaign Content:\n\n{parsed_html}\n\nDoes this email/creative comply with the regulations? Provide insights."

        try:
            # Generate response from the AI model
            response = model.generate_content(combined_prompt)
            st.write("Compliance Insights:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error generating insights: {e}")
    else:
        st.write("No relevant content found to compare for compliance.")
