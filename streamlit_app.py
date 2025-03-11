import streamlit as st
import google.generativeai as genai
import PyPDF2
import io
import os

# Configure your Gemini API key (store securely, e.g., Streamlit secrets)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Load your PDF compliance document (assuming it's in the same directory)
PDF_FILE_PATH = "compliance_document.pdf"

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ""  # Handle potential None returns
        return text
    except FileNotFoundError:
        st.error(f"PDF file not found at: {file_path}")
        return None
    except Exception as e:
        st.error(f"An error occurred while processing the PDF: {e}")
        return None

def generate_response(model, prompt):
    """Generates a response using the Gemini model."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")
        return "Sorry, I encountered an error. Please try again."

def main():
    st.title("Compliance Document Chatbot")

    # Load the PDF content
    pdf_content = extract_text_from_pdf(PDF_FILE_PATH)

    if pdf_content is None:
        return  # Stop execution if PDF loading failed

    model = genai.GenerativeModel('gemini-pro')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the compliance document"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            combined_prompt = f"Here is the compliance document text:\n\n{pdf_content}\n\nUser Question: {prompt}\n\nAnswer the user's question based on the document."
            response = generate_response(model, combined_prompt)
            full_response += response
            message_placeholder.markdown(full_response + "▌") #typing effect
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
