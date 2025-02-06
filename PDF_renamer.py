import os
import shutil
import re
import json
import io
import base64
from openai import OpenAI
from PyPDF2 import PdfReader, PdfWriter

# Define source and destination directories for PDF files.
SOURCE_DIR = r'C:\Users\Musta\Downloads\Documents\Thesis\Gem'
DESTINATION_DIR = r'C:\Users\Musta\Downloads\Documents\Thesis\Gem\renamed'

# Set your OpenAI API key.
api_key = "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"
client = OpenAI(api_key=api_key)

if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY.")

def extract_first_page_pdf_to_base64(pdf_path):
    """
    Extracts the first page of a PDF and converts it to a base64 string.
    """
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        buffer = io.BytesIO()
        writer.write(buffer)
        pdf_bytes = buffer.getvalue()
        base64_string = base64.b64encode(pdf_bytes).decode('utf-8')
        print(f"Extracted base64 string from the first page of: {pdf_path}")
        return base64_string
    except Exception as e:
        print(f"Error extracting base64 from {pdf_path}: {e}")
        return ""

def extract_first_page_text(pdf_path, max_chars=3000):
    """
    Extracts text from the first page of a PDF file.
    """
    try:
        print(f"Extracting text from the first page of: {pdf_path}")
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        text = page.extract_text()
        if text:
            extracted_text = text[:max_chars]
            print("Extracted text from PDF.")
            return extracted_text
        else:
            print("No text found on the first page.")
            return ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def infer_metadata(text):
    """
    Uses OpenAI's GPT-4o_mini to extract Author, Title, and Year from the text.
    The model is called with temperature=0 and instructed to return only valid JSON.
    """
    try:
        prompt = (
            "Extract the Author, Title, and Year of publication from the following text. "
            "Return ONLY valid JSON exactly in the following format without any additional text or markdown:\n\n"
            "{\n"
            '  "Author": "Author Name",\n'
            '  "Title": "Title of the Work",\n'
            '  "Year": "Year of Publication"\n'
            "}\n\n"
            f"{text}"
        )
        print("Sending prompt to OpenAI GPT-4o_mini with temperature=0...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        assistant_message = completion.choices[0].message.content
        assistant_message = re.sub(r'```json\n|\n```|```', '', assistant_message)
        print("Received response from OpenAI GPT-4o_mini:")
        print(assistant_message)
        metadata_json = json.loads(assistant_message)
        metadata = {
            "Author": metadata_json.get("Author", "NULL").strip(),
            "Title": metadata_json.get("Title", "NULL").strip(),
            "Year": metadata_json.get("Year", "NULL").strip()
        }
        return metadata
    except json.JSONDecodeError as jde:
        print(f"JSON Decode Error: {jde}")
        print("Assistant's response was not valid JSON.")
        print("Full response:", assistant_message)
        return {"Author": "NULL", "Title": "NULL", "Year": "NULL"}
    except Exception as e:
        print(f"Error during metadata inference: {e}")
        return {"Author": "NULL", "Title": "NULL", "Year": "NULL"}

def sanitize_string(s):
    """
    Removes characters that are invalid in file names.
    """
    return re.sub(r'[\\/*?:"<>|]', "", s)

def parse_authors(author_str):
    """
    Parses the author string into a list of authors.
    Checks for semicolons or " and " as delimiters.
    """
    if ';' in author_str:
        authors = [a.strip() for a in author_str.split(';') if a.strip()]
        return authors
    elif ' and ' in author_str:
        authors = [a.strip() for a in author_str.split(' and ') if a.strip()]
        return authors
    else:
        comma_count = author_str.count(',')
        words = author_str.split()
        if comma_count == 1:
            if len(words) > 3:
                authors = [a.strip() for a in author_str.split(',') if a.strip()]
                return authors
            else:
                return [author_str.strip()]
        elif comma_count > 1:
            authors = [a.strip() for a in author_str.split(',') if a.strip()]
            return authors
        else:
            return [author_str.strip()]

def reformat_single_author(author_str):
    """
    Converts "Last, First" format to "First Last" if needed.
    """
    if ',' in author_str:
        parts = [p.strip() for p in author_str.split(',')]
        if len(parts) >= 2:
            return f"{parts[1]} {parts[0]}"
    return author_str

def get_last_name(author):
    """
    Extracts the last name from a full author name.
    """
    author = author.strip()
    if ',' in author:
        return author.split(',')[0].strip()
    name_parts = author.split()
    if name_parts:
        return name_parts[-1].strip()
    return author

def rename_and_move_pdf(original_path, metadata, destination_root):
    """
    Renames and moves the PDF file based on the inferred metadata.
    The filename format is: <Author> <Year>--<Title>.pdf.
    If multiple authors are detected, the last name of the first author is used plus "et al.".
    """
    try:
        author_raw = sanitize_string(metadata["Author"])
        title = sanitize_string(metadata["Title"])
        year = sanitize_string(metadata["Year"])

        if not author_raw or author_raw.upper() == "NULL":
            new_filename_base = f"NULL-{year}-{title}"
        else:
            authors_list = parse_authors(author_raw)
            if len(authors_list) > 1:
                first_author = authors_list[0]
                last_name = get_last_name(first_author)
                author_citation = f"{last_name} et al."
            else:
                single_author = reformat_single_author(authors_list[0])
                author_citation = single_author
            new_filename_base = f"{author_citation} {year}--{title}"

        new_filename = new_filename_base
        if not new_filename.lower().endswith('.pdf'):
            new_filename += '.pdf'

        os.makedirs(destination_root, exist_ok=True)
        new_path = os.path.join(destination_root, new_filename)

        if os.path.exists(new_path):
            print(f"Duplicate file '{new_filename}' already exists. Skipping '{original_path}'.")
            return

        shutil.move(original_path, new_path)
        print(f"Moved: '{original_path}' -> '{new_path}'")
    except Exception as e:
        print(f"Error renaming/moving '{original_path}': {e}")

def process_pdf(pdf_path):
    """
    Processes a single PDF file.
    It extracts the first page (as base64 and text), infers metadata, and renames the file.
    """
    print(f"\nProcessing '{pdf_path}'...")
    base64_data = extract_first_page_pdf_to_base64(pdf_path)
    extracted_text = extract_first_page_text(pdf_path)
    if not extracted_text.strip():
        print(f"No text extracted from '{pdf_path}'. Skipping...")
        return
    metadata = infer_metadata(extracted_text)
    print(f"Inferred Metadata: {metadata}")
    rename_and_move_pdf(pdf_path, metadata, DESTINATION_DIR)

def process_directory():
    """
    Processes all PDF files in the source directory.
    """
    os.makedirs(DESTINATION_DIR, exist_ok=True)
    pdf_files = [f for f in os.listdir(SOURCE_DIR)
                 if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(SOURCE_DIR, f))]
    if not pdf_files:
        print(f"No PDF files found in {SOURCE_DIR}")
        return
    print(f"Found {len(pdf_files)} PDF files to process.")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\nProcessing file {i} of {len(pdf_files)}")
        pdf_path = os.path.join(SOURCE_DIR, pdf_file)
        process_pdf(pdf_path)
    print("\nProcessing complete!")

if __name__ == "__main__":
    print(f"Starting PDF processing from directory: {SOURCE_DIR}")
    print(f"Files will be moved to: {DESTINATION_DIR}")
    process_directory()
