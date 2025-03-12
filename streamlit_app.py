import streamlit as st
import google.generativeai as genai
import PyPDF2
from bs4 import BeautifulSoup
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import email
from email import policy
from email.parser import BytesParser

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

# Email Parsing function
def parse_email_content(email_file):
    try:
        msg = BytesParser(policy=policy.default).parse(email_file)
        # Extract plain text content of the email
        email_text = msg.get_body(preferencelist=('plain')).get_payload()
        return email_text
    except Exception as e:
        st.error(f"Error parsing email: {e}")
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
    embeddings = vectorizer.fit_transform(text_list)  # Fit on the combined text list (query + chunks)
    return embeddings, vectorizer

# Function to search for the most relevant text chunk
def find_most_relevant_chunk(query, chunks):
    # Combine the query and document chunks for consistent vectorization
    text_list = [query] + chunks
    embeddings, vectorizer = get_text_embeddings(text_list)
    
    # Extract the query's embedding (first row of embeddings)
    query_embedding = embeddings[0:1]  # First row corresponds to the query
    
    # The rest of the embeddings are for the document chunks
    chunk_embeddings = embeddings[1:]  # All except the first row
    
    # Calculate cosine similarity between query and document chunks
    similarities = cosine_similarity(query_embedding, chunk_embeddings)
    
    # Get the index of the most relevant chunk
    best_chunk_idx = np.argmax(similarities)
    
    return chunks[best_chunk_idx]

# Streamlit App UI
st.title("Mutual Fund Marketing Campaign Compliance Checker")

# Add custom CSS to hide the header and the top-right buttons
hide_streamlit_style = """
    <style>
        .css-1r6p8d1 {display: none;} /* Hides the Streamlit logo in the top left */
        .css-1v3t3fg {display: none;} /* Hides the star button */
        .css-1r6p8d1 .st-ae {display: none;} /* Hides the Streamlit logo */
        header {visibility: hidden;} /* Hides the header */
        .css-1tqja98 {visibility: hidden;} /* Hides the header bar */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Path to the pre-existing Compliance PDF Document
PDF_FILE_PATH = "compliance_document.pdf"  # Replace with the correct path to your compliance document
pdf_content = extract_text_from_pdf(PDF_FILE_PATH)

if pdf_content is None:
    st.stop()  # Stop execution if PDF loading failed

# Split the content into smaller chunks for semantic search
chunks = split_text_into_chunks(pdf_content)

# Upload HTML or Email Content
file_type = st.radio("Choose the file type", ('HTML Email', 'Text Email (.eml)'))

# Initialize parsed_html to None
parsed_html = None

if file_type == 'HTML Email':
    html_file = st.file_uploader("Upload HTML Email/Creative", type="html")
    if html_file is not None:
        html_content = html_file.read().decode("utf-8")
        parsed_html = parse_html_content(html_content)
        
        if parsed_html is None:
            st.stop()  # Stop execution if HTML parsing failed
else:
    email_file = st.file_uploader("Upload Email (.eml)", type="eml")
    if email_file is not None:
        parsed_html = parse_email_content(email_file)
        
        if parsed_html is None:
            st.stop()  # Stop execution if email parsing failed

# Check compliance for the uploaded content
if parsed_html:
    relevant_chunk = find_most_relevant_chunk(parsed_html, chunks)
    
    if relevant_chunk:
        # Load and configure the Generative AI Model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Create a combined prompt with the relevant content and HTML creative
        combined_prompt = f"Here is the most relevant content from the compliance document:\n\n{relevant_chunk}\n\nUser's Marketing Campaign Content:\n\n{parsed_html}\n\nDoes this email/creative comply with the regulations? Provide insights and specify which clauses are being followed or violated, including suggestions for improvement."

        try:
            # Generate response from the AI model
            response = model.generate_content(combined_prompt)
            st.write("Compliance Insights:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error generating insights: {e}")
    else:
        st.write("No relevant content found to compare for compliance.")
