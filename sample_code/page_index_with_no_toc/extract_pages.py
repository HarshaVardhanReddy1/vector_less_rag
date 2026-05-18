import pdfplumber
import json
import tiktoken


model_name = "gpt-oss-120b:free"
pdf_path = "docs/2023-annual-report.pdf"
output_path = "json_files/pdf_pages1.json"

def get_token_encoder(model_name):
    try:
        encoder = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoder = tiktoken.get_encoding("cl100k_base")
    return encoder

def extract_pages(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        encoder = get_token_encoder(model_name)
        pages_data = []

        for pages in pdf.pages:
            page_number = pages.page_number
            text = pages.extract_text() or ""
            token_count = len(encoder.encode(text))

            pages_data.append({
                "page": page_number,
                "page_text": text,
                "token_count": token_count
            })
    return pages_data

def save_pages_to_json(pages_data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=4, ensure_ascii=False)
    print("Pages data saved to", output_path)

if __name__ == "__main__":
    print("pages extraction started....")
    pages_data = extract_pages(pdf_path)
    print("extraction completed.")
    print()
    print("saving pages to json file started.......")
    save_pages_to_json(pages_data,output_path)
    print("saving json files completed.")

    