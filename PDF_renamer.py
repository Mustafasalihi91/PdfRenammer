# To install all required dependencies, run:
# pip install openai PyPDF2

import os
import shutil
import re
import json
import io
import base64
# Import the OpenAI module. Ensure the openai package is installed.
from openai import OpenAI
# Import classes for PDF processing. Install PyPDF2 if needed.
from PyPDF2 import PdfReader, PdfWriter

# ---------------------------------------------------------------------------
# Set your source and destination directories.
# Replace the placeholder paths with your actual directories.
# For example:
# SOURCE_DIR = r'/path/to/your/pdf/source/directory'
# DESTINATION_DIR = r'/path/to/your/pdf/destination/directory'
# ---------------------------------------------------------------------------
SOURCE_DIR = r'/path/to/your/source/directory'
DESTINATION_DIR = r'/path/to/your/destination/directory'

# ---------------------------------------------------------------------------
# Set your OpenAI API key.
# Replace "YOUR_API_KEY_HERE" with your actual OpenAI API key.
# DO NOT commit your real API key to a public repository.
# ---------------------------------------------------------------------------
api_key = "YOUR_API_KEY_HERE"
client = OpenAI(api_key=api_key)

if not api_key:
    raise ValueError("OpenAI API key not found. Please set the api_key variable.")

# ---------------------------------------------------------------------------
# Function: extract_first_page_pdf_to_base64
#
# Extracts the first page of a PDF and returns it as a base64 encoded string.
# This is useful if you need to send the page as a compact string.
# ---------------------------------------------------------------------------
def extract_first_page_pdf_to_base64(pdf_path):
    try:
        # Read the PDF file.
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        # Add the first page to the writer.
        writer.add_page(reader.pages[0])
        # Write the page to a bytes buffer.
        buffer = io.BytesIO()
        writer.write(buffer)
        pdf_bytes = buffer.getvalue()
        # Encode the bytes to a base64 string.
        base64_string = base64.b64encode(pdf_bytes).decode('utf-8')
        print(f"Extracted base64 string from the first page of: {pdf_path}")
        return base64_string
    except Exception as e:
        print(f"Error extracting base64 from {pdf_path}: {e}")
        return ""

# ---------------------------------------------------------------------------
# Function: extract_first_page_text
#
# Extracts text from the first page of a PDF.
# Limits the text to a maximum number of characters (default 3000).
# ---------------------------------------------------------------------------
def extract_first_page_text(pdf_path, max_chars=3000):
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

# ---------------------------------------------------------------------------
# Function: infer_metadata
#
# Uses OpenAI's model to extract metadata (Author, Title, Year) from the given text.
# The model is called with temperature=0 to ensure consistent output.
# The response should be valid JSON in a fixed format.
# ---------------------------------------------------------------------------
def infer_metadata(text):
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
        # Get the response message from the assistant.
        assistant_message = completion.choices[0].message.content
        # Remove any markdown formatting if present.
        assistant_message = re.sub(r'```json\n|\n```|```', '', assistant_message)
        print("Received response from OpenAI GPT-4o_mini:")
        print(assistant_message)
        # Parse the assistant's message into JSON.
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

# ---------------------------------------------------------------------------
# Function: sanitize_string
#
# Removes characters that are not allowed in file names.
# ---------------------------------------------------------------------------
def sanitize_string(s):
    return re.sub(r'[\\/*?:"<>|]', "", s)

# ---------------------------------------------------------------------------
# Function: parse_authors
#
# Parses a string of authors into a list.
# Checks for common delimiters such as semicolons or the word " and ".
# ---------------------------------------------------------------------------
def parse_authors(author_str):
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

# ---------------------------------------------------------------------------
# Function: reformat_single_author
#
# Converts "Last, First" to "First Last" if necessary.
# ---------------------------------------------------------------------------
def reformat_single_author(author_str):
    if ',' in author_str:
        parts = [p.strip() for p in author_str.split(',')]
        if len(parts) >= 2:
            return f"{parts[1]} {parts[0]}"
    return author_str

# ---------------------------------------------------------------------------
# Function: get_last_name
#
# Extracts the last name from a full author name.
# ---------------------------------------------------------------------------
def get_last_name(author):
    author = author.strip()
    if ',' in author:
        return author.split(',')[0].strip()
    name_parts = author.split()
    if name_parts:
        return name_parts[-1].strip()
    return author

# ---------------------------------------------------------------------------
# Function: rename_and_move_pdf
#
# Renames and moves the PDF file based on the inferred metadata.
# The new file name follows the format: <Author> <Year>--<Title>.pdf.
# If multiple authors exist, uses the last name of the first author plus "et al.".
# ---------------------------------------------------------------------------
def rename_and_move_pdf(original_path, metadata, destination_root):
    try:
        # Remove invalid characters from metadata strings.
        author_raw = sanitize_string(metadata["Author"])
        title = sanitize_string(metadata["Title"])
        year = sanitize_string(metadata["Year"])

        # Build the new file name.
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

        # Append .pdf extension if not already present.
        new_filename = new_filename_base
        if not new_filename.lower().endswith('.pdf'):
            new_filename += '.pdf'

        # Ensure the destination directory exists.
        os.makedirs(destination_root, exist_ok=True)
        new_path = os.path.join(destination_root, new_filename)

        # Check for duplicates.
        if os.path.exists(new_path):
            print(f"Duplicate file '{new_filename}' already exists. Skipping '{original_path}'.")
            return

        # Move the file to the destination with the new name.
        shutil.move(original_path, new_path)
        print(f"Moved: '{original_path}' -> '{new_path}'")
    except Exception as e:
        print(f"Error renaming/moving '{original_path}': {e}")

# ---------------------------------------------------------------------------
# Function: process_pdf
#
# Processes a single PDF file by extracting the first page as both text and
# a base64 string, inferring metadata from the text, and renaming/moving the file.
# ---------------------------------------------------------------------------
def process_pdf(pdf_path):
    print(f"\nProcessing '{pdf_path}'...")
    # Extract the first page as a base64 string.
    base64_data = extract_first_page_pdf_to_base64(pdf_path)
    # Extract text from the first page.
    extracted_text = extract_first_page_text(pdf_path)
    if not extracted_text.strip():
        print(f"No text extracted from '{pdf_path}'. Skipping...")
        return
    # Infer metadata from the extracted text.
    metadata = infer_metadata(extracted_text)
    print(f"Inferred Metadata: {metadata}")
    # Rename and move the file based on the metadata.
    rename_and_move_pdf(pdf_path, metadata, DESTINATION_DIR)

# ---------------------------------------------------------------------------
# Function: process_directory
#
# Processes all PDF files in the source directory.
# Iterates over each file and calls process_pdf.
# ---------------------------------------------------------------------------
def process_directory():
    # Ensure the destination directory exists.
    os.makedirs(DESTINATION_DIR, exist_ok=True)
    # List all PDF files in the source directory.
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

# ---------------------------------------------------------------------------
# Main block: Executes the script when run directly.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting PDF processing from directory: {SOURCE_DIR}")
    print(f"Files will be moved to: {DESTINATION_DIR}")
    process_directory()
