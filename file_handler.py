from pypdf import PdfReader
from datetime import datetime,timezone
from docx import Document
from uuid import uuid4
from search import save_embedding_to_search


def read_docx(file_path):
    document = Document(file_path)
    return [paragraph.text for paragraph in document.paragraphs]

def read_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        return [page.extract_text() for page in reader.pages]

def convert_file_to_text(pdf_file_path, request_id, only_text=False):
    page_list = []
    if pdf_file_path.endswith(".docx"):
        page_list = read_docx(pdf_file_path)
    elif pdf_file_path.endswith(".pdf"):
        page_list = read_pdf(pdf_file_path)
    if only_text:
        return ' '.join(page_list)
    current_time = datetime.now(timezone.utc).isoformat()  # Get current time in ISO format
    all_pages_text = [{
        "Seitenzahl": idx+1, "id": f"{uuid4()}", "Dateiname": pdf_file_path.split("/")[-1],
        "text": page, "requestId": request_id,"timeStamp": current_time  # Add current timestamp
    } for idx, page in enumerate(page_list)]
    return all_pages_text

def save_file_to_search(filename, request_id):
    documents = convert_file_to_text(filename, request_id)
    save_embedding_to_search(documents)

if __name__ == "__main__":
    pass