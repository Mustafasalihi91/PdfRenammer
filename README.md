# Markdown & PDF Renamer 📄🔄

This project provides two Python scripts that rename Markdown and PDF files based on their content. Both scripts use the OpenAI API to infer metadata—such as Author, Title, and Year—from the files. The new file name follows this format:

```
<Author> <Year>--<Title>.<ext>
```

## Features ✨

- **Markdown Renamer:**  
  Extracts text from the start of a Markdown file, infers metadata, and renames the file with the `.md` extension.

- **PDF Renamer:**  
  Extracts text and the first page as a base64 string from a PDF file, infers metadata, and renames the file with the `.pdf` extension.

## Prerequisites 🔑

- Python 3.6 or later
- An OpenAI API key

## Installation 🛠

Clone this repository and install the required dependencies:

```bash
pip install openai PyPDF2
```

## Configuration ⚙️

Before running the scripts, update the configuration in the code:

- **Source Directory:**  
  Set the path where your original Markdown or PDF files are stored.

- **Destination Directory:**  
  Set the path where renamed files will be moved.

- **API Key:**  
  Replace `"YOUR_API_KEY_HERE"` with your actual OpenAI API key. **Do not commit your real API key to a public repository.**

Example configuration snippet:

```python
# Replace the placeholder paths with your actual directories.
SOURCE_DIR = r'/path/to/your/source/directory'
DESTINATION_DIR = r'/path/to/your/destination/directory'

# Replace "YOUR_API_KEY_HERE" with your actual OpenAI API key.
api_key = "YOUR_API_KEY_HERE"
```

## Usage 🚀

Run the desired script by excecuting from the IDE or by using the command line:

- For the Markdown renamer:

  ```bash
  python markdown_renamer.py
  ```

- For the PDF renamer:

  ```bash
  python pdf_renamer.py
  ```

Each script will process all files in the source directory, infer metadata using OpenAI's API, and then rename and move the files to the destination directory.

## How It Works 📝

Both scripts share similar functionality:

1. **Text Extraction:**  
   The script reads the file and extracts a portion of the text. For PDFs, it also extracts the first page as a base64 encoded string.

2. **Metadata Inference:**  
   The OpenAI API is called with a prompt to extract the Author, Title, and Year from the text.

3. **File Name Sanitization:**  
   The scripts remove any characters that are invalid in file names.

4. **Renaming & Moving:**  
   The file is renamed using the format `<Author> <Year>--<Title>.<ext>` and moved to the destination directory. If a file with the new name already exists, it skips that file.

Each function in the code includes comments that explain its purpose.

## Caution ⚠️

Keep your API key secure. Do not expose it in public repositories or share it with others.

---

Enjoy using these tools to easily organize your Markdown and PDF files! 😎📂
