import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

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

# Function to search for relevant content based on a query
def search_relevant_text(pdf_text, query):
    # Search for sections of the document that contain relevant text
    # Simple approach: search for the query word/phrase in the document
    pattern = re.compile(r"([^.]*?{}[^.]*\.)".format(re.escape(query)), re.IGNORECASE)
    matches = pattern.findall(pdf_text)
    return " ".join(matches)

# Streamlit App UI
st.title("Compliance Document Chatbot (Gemini 1.5 Flash)")

# Load PDF content (replace with your PDF file path)
PDF_FILE_PATH = "compliance_document.pdf"  # Replace with your PDF path
pdf_content = extract_text_from_pdf(PDF_FILE_PATH)

if pdf_content is None:
    st.stop()  # Stop execution if PDF loading failed

# Prompt input field
prompt = st.text_input("Ask a question about the compliance document:", "")

# Button to generate response
if st.button("Generate Response"):
    if prompt:
        try:
            # Search for relevant content based on the prompt
            relevant_content = search_relevant_text(pdf_content, prompt)
            
            if not relevant_content:
                st.write("No relevant content found for your question.")
            else:
                # Load and configure the model
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Create a combined prompt with the relevant content and user question
                combined_prompt = f"Here is the relevant content from the compliance document:\n\n{relevant_content}\n\nUser Question: {prompt}\n\nAnswer the user's question based on the relevant content."

                # Generate response from the model
                response = model.generate_content(combined_prompt)

                # Display response in Streamlit
                st.write("Response:")
                st.write(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a prompt.")
