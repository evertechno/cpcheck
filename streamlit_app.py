import streamlit as st
import google.generativeai as genai
import PyPDF2

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
            # Load and configure the model
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Create a combined prompt with the PDF content and user question
            combined_prompt = f"Here is the compliance document text:\n\n{pdf_content}\n\nUser Question: {prompt}\n\nAnswer the user's question based on the document."

            # Generate response from the model
            response = model.generate_content(combined_prompt)

            # Display response in Streamlit
            st.write("Response:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a prompt.")
