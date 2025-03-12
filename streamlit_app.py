import streamlit as st
import pandas as pd
import requests
import asyncio
import PyPDF2  # Library to extract text from PDF
from io import BytesIO
from googletrans import Translator
from fpdf import FPDF
import os
import re

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Helper Functions
def extract_amfi_guidelines_from_local_pdf(pdf_path):
    """Extract AMFI guidelines from a local PDF."""
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def dynamic_compliance_check(test_email, amfi_guidelines):
    """Dynamically check the email for compliance based on AMFI guidelines."""
    violations = []

    # Define patterns for common violations
    required_keywords = ["mutual fund", "disclaimer", "risk", "past performance", "no guarantee"]
    guideline_keywords = re.findall(r'\b(?:' + '|'.join(required_keywords) + r')\b', amfi_guidelines.lower())

    # Check if essential terms are mentioned in the email
    if not any(keyword in test_email.lower() for keyword in required_keywords):
        violations.append("The email must mention key terms like 'mutual fund', 'disclaimer', 'risk', or 'past performance'.")

    # Ensure risk, disclaimer, and past performance terms are mentioned
    if not any(term in test_email.lower() for term in ["risk", "past performance", "no guarantee"]):
        violations.append("The email should include a disclaimer regarding the risks involved and past performance of the mutual fund.")

    # Check if the disclaimer is generic enough or violates specific AMFI rules
    if re.search(r"(guarantee|promise|assurance)", test_email.lower()):
        violations.append("The email should not include any guarantees or promises regarding returns.")

    # Additional checks: Look for references to funds, financial advice, etc.
    if re.search(r"(investment|advice|returns|profits)", test_email.lower()):
        violations.append("The email should clarify that it does not provide financial advice or guaranteed returns.")

    if violations:
        return False, violations
    return True, ["The email complies with the code of conduct."]

def generate_pdf_report(content, insights, compliance_score):
    """Generate a PDF report with the content, insights, and compliance score."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Compliance Check Report", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Compliance Check Insights:\n\n{insights}")

    pdf.ln(10)
    pdf.cell(200, 10, f"Compliance Score: {compliance_score}%")

    pdf.ln(10)
    pdf.multi_cell(0, 10, "Original Content:\n\n" + content)

    file_path = "compliance_report.pdf"
    pdf.output(file_path)
    return file_path

def generate_text_report(content, insights, compliance_score):
    """Generate a text file report with the content, insights, and compliance score."""
    report = f"Compliance Check Report\n\n"
    report += f"Compliance Insights:\n{insights}\n\n"
    report += f"Compliance Score: {compliance_score}%\n\n"
    report += f"Original Content:\n{content}\n"

    file_path = "compliance_report.txt"
    with open(file_path, "w") as f:
        f.write(report)
    return file_path

def send_email(email, subject, body, api_key):
    """Function to send email using Mailgun API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "from": "Your Company <youremail@example.com>",
        "to": email,
        "subject": subject,
        "text": body
    }
    try:
        response = requests.post("https://api.mailgun.net/v3/yourdomain.com/messages", headers=headers, data=data)
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending email: {e}")
        return False

async def translate_text(text, target_language):
    """Translate the email content to the target language."""
    translator = Translator()
    translated = translator.translate(text, dest=target_language)
    return translated.text

# Streamlit App
st.title("Mutual Fund Compliance & Email Campaign Tool")

# Select function to use
tool_choice = st.radio("Choose a tool:", ["Compliance Checker", "Email Campaign Tool"])

if tool_choice == "Compliance Checker":
    st.header("Mutual Fund Marketing Campaign Compliance Checker")
    
    # Load AMFI Guidelines from local PDF
    AMFI_PDF_PATH = "AMFI.pdf"  # Assuming the PDF is in the same directory as your app code
    amfi_guidelines = extract_amfi_guidelines_from_local_pdf(AMFI_PDF_PATH)
    
    if amfi_guidelines:
        st.text_area("AMFI Advertisement Code Guidelines", amfi_guidelines, height=300)

    # Allow the user to upload or enter content for compliance checking
    content_type = st.radio("Select content type:", ["Email", "HTML", "PDF"])
    
    if content_type == "Email":
        test_email_message = st.text_area("Enter your test email message", height=300)
        if st.button("Check Compliance"):
            if test_email_message:
                is_compliant, feedback = dynamic_compliance_check(test_email_message, amfi_guidelines)
                if is_compliant:
                    st.success("The email complies with the AMFI Code of Conduct.")
                else:
                    st.warning("The email has the following issues:")
                    for issue in feedback:
                        st.warning(issue)

    elif content_type == "HTML":
        html_file = st.file_uploader("Upload HTML Email", type="html")
        if html_file is not None:
            html_content = html_file.read().decode("utf-8")
            is_compliant, feedback = dynamic_compliance_check(html_content, amfi_guidelines)
            if is_compliant:
                st.success("The HTML email complies with the AMFI Code of Conduct.")
            else:
                st.warning("The HTML email has the following issues:")
                for issue in feedback:
                    st.warning(issue)

    elif content_type == "PDF":
        pdf_file = st.file_uploader("Upload PDF File", type="pdf")
        if pdf_file is not None:
            try:
                reader = PyPDF2.PdfReader(pdf_file)
                pdf_text = ""
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    pdf_text += page.extract_text()
                is_compliant, feedback = dynamic_compliance_check(pdf_text, amfi_guidelines)
                if is_compliant:
                    st.success("The PDF complies with the AMFI Code of Conduct.")
                else:
                    st.warning("The PDF has the following issues:")
                    for issue in feedback:
                        st.warning(issue)
            except Exception as e:
                st.error(f"Error processing PDF: {e}")

elif tool_choice == "Email Campaign Tool":
    st.header("AI Powered Email Campaign Tool")

    user_key = st.text_input("Enter your API key to access the app:", type="password")
    if user_key != st.secrets["api_keys"].get("key_1"):  # Ensure the API key is correct
        st.error("Invalid API Key! Access Denied.")
    else:
        # Upload CSV file containing emails
        uploaded_file = st.file_uploader("Upload CSV file (columns: email, first_name)", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if 'email' not in df.columns or 'first_name' not in df.columns:
                st.error("CSV must contain 'email' and 'first_name' columns.")
            else:
                email_list = df['email'].tolist()
                first_name_list = df['first_name'].tolist()

                subject = st.text_input("Email Subject", "Your Newsletter")
                body_template = "Hello {first_name},\n\nWe have some exciting news for you. Stay tuned!"
                email_body = st.text_area("Email Body", body_template)

                # Translate email content if needed
                language_options = ["en", "es", "fr", "de", "it", "pt", "ru"]
                selected_language = st.selectbox("Select Email Language", language_options)

                if selected_language != "en":
                    translated_body = asyncio.run(translate_text(email_body, selected_language))
                    st.session_state.translated_body = translated_body

                # Preview email
                preview_email = st.checkbox("Preview Email with First Record")
                if preview_email and len(email_list) > 0:
                    preview_text = st.session_state.translated_body if 'translated_body' in st.session_state else email_body
                    preview_text = preview_text.format(first_name=first_name_list[0])
                    st.write("Preview:")
                    st.write(preview_text)

                # Send emails
                if st.checkbox("Confirm and Send Campaign"):
                    api_key = st.secrets["MAILGUN_API_KEY"]
                    success_count = 0
                    failure_count = 0
                    for email, first_name in zip(email_list, first_name_list):
                        personalized_body = st.session_state.translated_body if 'translated_body' in st.session_state else email_body
                        personalized_body = personalized_body.format(first_name=first_name)
                        if send_email(email, subject, personalized_body, api_key):
                            success_count += 1
                        else:
                            failure_count += 1

                    st.success(f"Emails sent successfully: {success_count}")
                    if failure_count > 0:
                        st.warning(f"Emails failed to send: {failure_count}")
