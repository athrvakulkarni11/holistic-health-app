import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    """Extract text from a given PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Example usage
pdf_file = "Jersey Size and Name (Responses) - Sheet2.pdf"  # Replace with your PDF file path
extracted_text = extract_text_from_pdf(pdf_file)
# print(extracted_text)
with open("output.txt", "w") as f:
    f.write(extracted_text)

