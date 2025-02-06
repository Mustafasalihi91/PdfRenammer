import os
import shutil
import re
import json
from openai import OpenAI  # Import the OpenAI client from the openai package

# ---------------------------------------------------------------------------
# Configuration Section
# ---------------------------------------------------------------------------

# Set the path to the directory containing your Markdown files.
# Replace 'path/to/source/directory' with your own directory path.
SOURCE_DIR = r'path/to/source/directory'

# Set the path to the directory where the renamed Markdown files will be stored.
# Replace 'path/to/destination/directory' with your own directory path.
DESTINATION_DIR = r'path/to/destination/directory'

# Set your OpenAI API key.
# Replace 'your-api-key-here' with your actual API key.
# Alternatively, load the key from an environment variable or a secure file.
api_key = "your-api-key-here"

# Create an instance of the OpenAI client with the provided API key.
client = OpenAI(api_key=api_key)

# Ensure that an API key is provided.
if not api_key:
    raise ValueError("OpenAI API key not found. Please set your API key in the configuration section.")

# ---------------------------------------------------------------------------
# End of Configuration Section
# ---------------------------------------------------------------------------

def extract_first_section_text(md_path, max_chars=3000):
    """
    Extract text from the beginning of a Markdown file.

    Parameters:
        md_path (str): The file path to the Markdown file.
        max_chars (int): Maximum number of characters to extract.

    Returns:
        str: The extracted text or an empty string on error.
    """
    try:
        print(f"Reading text from: {md_path}")

        # Open the file with UTF-8 encoding and read its contents.
        with open(md_path, 'r', encoding='utf-8') as file:
            full_text = file.read()

        # Check if the file contains any text.
        if not full_text:
            print("No text found in the Markdown file.")
            return ""

        # Extract the first max_chars characters.
        extracted_text = full_text[:max_chars]
        print("Extracted text from the Markdown file.")
        return extracted_text

    except Exception as e:
        # Print error information if the file cannot be read.
        print(f"Error reading text from {md_path}: {e}")
        return ""

def infer_metadata(text):
    """
    Use OpenAI's API to extract metadata (Author, Title, Year) from text.

    Parameters:
        text (str): Text from which to extract metadata.

    Returns:
        dict: A dictionary with keys "Author", "Title", and "Year".
    """
    try:
        # Prepare the prompt for the API.
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
        print("Sending prompt to OpenAI GPT-4 with temperature=0...")

        # Call the API to generate a response.
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        # Extract the assistant's message from the response.
        assistant_message = completion.choices[0].message.content

        # Remove any markdown code block formatting from the response.
        assistant_message = re.sub(r"```(?:json)?\n", "", assistant_message)
        assistant_message = re.sub(r"```", "", assistant_message)

        print("Received response from OpenAI GPT-4:")
        print(assistant_message)

        # Parse the JSON from the assistant's message.
        metadata_json = json.loads(assistant_message)

        # Build a clean metadata dictionary.
        metadata = {
            "Author": metadata_json.get("Author", "NULL").strip(),
            "Title": metadata_json.get("Title", "NULL").strip(),
            "Year": metadata_json.get("Year", "NULL").strip()
        }
        return metadata

    except json.JSONDecodeError as jde:
        # Handle errors if the response is not valid JSON.
        print(f"JSON Decode Error: {jde}")
        print("Assistant's response was not valid JSON.")
        print("Full response:", assistant_message)
        return {"Author": "NULL", "Title": "NULL", "Year": "NULL"}

    except Exception as e:
        # Handle any other exceptions that occur during the API call.
        print(f"Error during metadata inference: {e}")
        return {"Author": "NULL", "Title": "NULL", "Year": "NULL"}

def sanitize_string(s):
    """
    Remove characters that are invalid in file names.

    Parameters:
        s (str): The string to sanitize.

    Returns:
        str: The sanitized string.
    """
    return re.sub(r'[\\/*?:"<>|]', "", s)

def parse_authors(author_str):
    """
    Split a string of authors into a list of individual authors.

    Parameters:
        author_str (str): A string that lists authors.

    Returns:
        list: A list of individual author names.
    """
    if ';' in author_str:
        # Split authors using semicolons.
        authors = [a.strip() for a in author_str.split(';') if a.strip()]
        return authors
    elif ' and ' in author_str:
        # Split authors using the word "and".
        authors = [a.strip() for a in author_str.split(' and ') if a.strip()]
        return authors
    else:
        comma_count = author_str.count(',')
        words = author_str.split()
        if comma_count == 1:
            # If there is one comma and the string is long, assume multiple authors.
            if len(words) > 3:
                authors = [a.strip() for a in author_str.split(',') if a.strip()]
                return authors
            else:
                return [author_str.strip()]
        elif comma_count > 1:
            # Split authors using commas.
            authors = [a.strip() for a in author_str.split(',') if a.strip()]
            return authors
        else:
            # Return the string as a single author.
            return [author_str.strip()]

def reformat_single_author(author_str):
    """
    Reformat an author's name from "Last, First" to "First Last".

    Parameters:
        author_str (str): The author name string.

    Returns:
        str: The reformatted author name.
    """
    if ',' in author_str:
        parts = [p.strip() for p in author_str.split(',')]
        if len(parts) >= 2:
            return f"{parts[1]} {parts[0]}"
    return author_str

def get_last_name(author):
    """
    Extract the last name from a full author name.

    Parameters:
        author (str): The full author name.

    Returns:
        str: The last name.
    """
    author = author.strip()
    if ',' in author:
        return author.split(',')[0].strip()
    name_parts = author.split()
    if name_parts:
        return name_parts[-1].strip()
    return author

def rename_and_move_markdown(original_path, metadata, destination_root):
    """
    Rename a Markdown file based on its metadata and move it to a new directory.

    The new filename format is: <Author> <Year>--<Title>.md.
    For multiple authors, use the last name of the first author followed by "et al."
    For a single author, reformat the name if it is in "Last, First" format.

    Parameters:
        original_path (str): The current file path.
        metadata (dict): A dictionary containing "Author", "Title", and "Year".
        destination_root (str): The directory where the file should be moved.
    """
    try:
        # Remove invalid characters from metadata values.
        author_raw = sanitize_string(metadata["Author"])
        title = sanitize_string(metadata["Title"])
        year = sanitize_string(metadata["Year"])

        # Build the new filename based on the metadata.
        if not author_raw or author_raw.upper() == "NULL":
            new_filename_base = f"NULL-{year}-{title}"
        else:
            authors_list = parse_authors(author_raw)
            if len(authors_list) > 1:
                # Use the last name of the first author followed by "et al." if multiple authors exist.
                first_author = authors_list[0]
                last_name = get_last_name(first_author)
                author_citation = f"{last_name} et al."
            else:
                # For a single author, reformat if the name is in "Last, First" format.
                single_author = reformat_single_author(authors_list[0])
                author_citation = single_author
            new_filename_base = f"{author_citation} {year}--{title}"

        # Ensure the new filename ends with the .md extension.
        new_filename = new_filename_base
        if not new_filename.lower().endswith('.md'):
            new_filename += '.md'

        # Create the destination directory if it does not exist.
        os.makedirs(destination_root, exist_ok=True)
        new_path = os.path.join(destination_root, new_filename)

        # If a file with the new filename already exists, skip moving the file.
        if os.path.exists(new_path):
            print(f"Duplicate file with filename '{new_filename}' already exists. Skipping '{original_path}'.")
            return

        # Move (and rename) the file to the new destination.
        shutil.move(original_path, new_path)
        print(f"Moved: '{original_path}' -> '{new_path}'")
    except Exception as e:
        # Print error details if the file cannot be renamed or moved.
        print(f"Error renaming/moving '{original_path}': {e}")

def process_markdown(md_path):
    """
    Process a single Markdown file: extract text, infer metadata,
    and rename/move the file based on the metadata.

    Parameters:
        md_path (str): The file path to the Markdown file.
    """
    print(f"\nProcessing '{md_path}'...")

    # Extract text from the file.
    extracted_text = extract_first_section_text(md_path)
    if not extracted_text.strip():
        print(f"No text extracted from '{md_path}'. Skipping...")
        return

    # Use OpenAI to infer metadata from the extracted text.
    metadata = infer_metadata(extracted_text)
    print(f"Inferred Metadata: {metadata}")

    # Rename and move the file based on the inferred metadata.
    rename_and_move_markdown(md_path, metadata, DESTINATION_DIR)

def process_directory():
    """
    Process all Markdown files in the source directory.
    """
    # Ensure the destination directory exists.
    os.makedirs(DESTINATION_DIR, exist_ok=True)

    # List all files in the source directory with Markdown extensions.
    md_files = [
        f for f in os.listdir(SOURCE_DIR)
        if f.lower().endswith(('.md', '.markdown'))
        and os.path.isfile(os.path.join(SOURCE_DIR, f))
    ]

    # Check if any Markdown files are found.
    if not md_files:
        print(f"No Markdown files found in {SOURCE_DIR}")
        return

    print(f"Found {len(md_files)} Markdown files to process.")

    # Process each Markdown file one by one.
    for i, md_file in enumerate(md_files, 1):
        print(f"\nProcessing file {i} of {len(md_files)}")
        md_path = os.path.join(SOURCE_DIR, md_file)
        process_markdown(md_path)

    print("\nProcessing complete!")

if __name__ == "__main__":
    # Entry point for the script.
    print(f"Starting Markdown processing from directory: {SOURCE_DIR}")
    print(f"Files will be moved to: {DESTINATION_DIR}")
    process_directory()
