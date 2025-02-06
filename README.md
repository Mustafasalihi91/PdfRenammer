# Markdown & PDF Renamer 📄🔄

Where `<Author(s)>` intelligently handles single and multiple authors (using "et al." for multiple authors).

## Features ✨

*   **Intelligent Renaming:** Uses OpenAI's `gpt-4o-mini` model (with `temperature=0` for consistent results) to accurately extract metadata (Author, Title, Year) directly from the file content. No manual metadata entry is required!
*   **Markdown Support:**  Processes `.md` and `.markdown` files.  Extracts the initial text from the Markdown file for metadata analysis.
*   **PDF Support:**  Processes `.pdf` files.  Extracts *both* the text content of the first page and the first page itself (as a base64 encoded string) for robust metadata analysis.
*   **Multiple Author Handling:**  Correctly parses and formats author names, including:
    *   Single authors (e.g., "Jane Doe")
    *   "Last, First" format (automatically converted to "First Last")
    *   Multiple authors separated by commas, semicolons, or "and"
    *   Uses "et al." for multiple authors in the filename (e.g., "Doe et al.")
*   **Duplicate File Prevention:**  Checks for existing files with the generated name in the destination directory and skips renaming to avoid overwriting.
*   **Filename Sanitization:**  Removes invalid filename characters (e.g., `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) to ensure cross-platform compatibility.
*   **Clear Output:**  Provides detailed console output, showing the progress of file processing, extracted metadata, and any errors encountered.
*   **Error Handling:**  Includes robust error handling for:
    *   Missing or invalid OpenAI API keys.
    *   File reading and writing errors.
    *   JSON decoding errors from the OpenAI API response.
    *   Cases where no text can be extracted from a file.
*   **Well-Documented Code:** Each function has detailed docstrings explaining its purpose, parameters, and return values.  The code itself is heavily commented for clarity.

## Prerequisites 🔑

*   **Python 3.6+:**  Ensure you have a compatible Python version installed.
*   **OpenAI API Key:** You'll need an active OpenAI API key.  You can obtain one from the [OpenAI website](https://platform.openai.com/).
*   **Required Libraries:**
    *   `openai`: For interacting with the OpenAI API.
    *   `PyPDF2`: For reading PDF files.

## Installation 🛠

1.  **Clone this Repository:**

    ```bash
    git clone https://github.com/Mustafasalihi91/PdfRenammer.git
    cd PdfRenammer
    ```

2.  **Install Dependencies:**

    ```bash
    pip install openai PyPDF2
    ```

## Configuration ⚙️

1.  **Edit the Scripts:** Open `markdown_renamer.py` or `pdf_renamer.py` in a text editor or IDE.

2.  **Set Directories:**
    *   **`SOURCE_DIR`:**  Replace `'path/to/source/directory'` with the *absolute path* to the directory containing your Markdown or PDF files.  *Use raw strings (prefix with `r`) to avoid issues with backslashes in Windows paths.*  Example:
        ```python
        SOURCE_DIR = r'C:\Users\YourName\Documents\MyFiles'
        ```
    *   **`DESTINATION_DIR`:** Replace `'path/to/destination/directory'` with the *absolute path* to the directory where you want the renamed files to be saved. Example:
        ```python
        DESTINATION_DIR = r'C:\Users\YourName\Documents\RenamedFiles'
        ```

3.  **Set API Key:**
    *   **`api_key`:** Replace `"your-api-key-here"` with your actual OpenAI API key.  **IMPORTANT:**  *Never* commit your API key directly into a public repository!  Consider using environment variables (see the "Security Note" below).  Example (direct, but *not recommended* for public repos):
        ```python
        api_key = "sk-..."  # Your actual key
        ```

## Usage 🚀

1.  **Navigate to the Script Directory:**  Open a terminal or command prompt and use `cd` to navigate to the directory where you cloned the repository (the directory containing the `.py` files).

2.  **Run the Script:**

    *   **For Markdown Files:**
        ```bash
        python markdown_renamer.py
        ```
    *   **For PDF Files:**
        ```bash
        python pdf_renamer.py
        ```

The script will:

*   Scan the `SOURCE_DIR` for files with the appropriate extension (`.md` or `.markdown` for Markdown; `.pdf` for PDF).
*   For each file:
    *   Extract text (and the first page as base64 for PDFs).
    *   Send the extracted content to the OpenAI API to infer the Author, Title, and Year.
    *   Construct the new filename.
    *   Move the file to the `DESTINATION_DIR`, renaming it in the process.
*   Print informative messages to the console, including the inferred metadata and any errors.

## How It Works (Detailed Explanation) 📝

Both scripts follow a similar process:

1.  **File Discovery:**  The `process_directory()` function finds all Markdown or PDF files within the specified `SOURCE_DIR`.

2.  **File Processing:**  For each file, the `process_markdown()` or `process_pdf()` function is called.

3.  **Content Extraction:**
    *   **Markdown:** `extract_first_section_text()` reads the beginning of the Markdown file (up to `max_chars`, default 3000 characters) to get the relevant text for metadata inference.
    *   **PDF:**
        *   `extract_first_page_text()` extracts the text content from the first page of the PDF.
        *   `extract_first_page_pdf_to_base64()` extracts the *entire* first page and converts it to a base64 encoded string. This is useful if the text extraction fails or provides insufficient information.

4.  **Metadata Inference (OpenAI API Call):**  The `infer_metadata()` function is the core of the renaming process.  It:
    *   Constructs a prompt for the OpenAI API, instructing it to extract the Author, Title, and Year from the provided text and return the result *only* as a JSON object.
    *   Calls the OpenAI API using the `gpt-4o-mini` model with `temperature=0`.  Setting `temperature=0` ensures consistent and deterministic results.
    *   Parses the JSON response from the API.
    *   Handles potential `JSONDecodeError` exceptions, returning default "NULL" values if the API response is invalid.
    *   Returns a dictionary containing the extracted metadata (Author, Title, Year).

5.  **Filename Construction:** The `rename_and_move_markdown()` or `rename_and_move_pdf()` function takes the inferred metadata and constructs the new filename:
    *   `sanitize_string()` removes any characters that are invalid in filenames.
    *   `parse_authors()` handles various author string formats (single author, multiple authors separated by commas, semicolons, or "and").
    *   `reformat_single_author()` converts "Last, First" names to "First Last".
    *   `get_last_name()` extracts the last name from an author string.
    *   The filename is assembled in the format `<Author(s)> <Year>--<Title>.<ext>`.

6.  **File Renaming and Moving:**
    *   The script checks if a file with the generated filename already exists in the `DESTINATION_DIR`. If it does, the file is skipped to prevent overwriting.
    *   `shutil.move()` renames and moves the file to the `DESTINATION_DIR`.
    *   Handles potential exceptions during the file move operation.

## Security Note (API Key Management) 🔑🛡️

1.  **Set the Environment Variable:**
    *   **Windows:**
        ```bash
        setx OPENAI_API_KEY "your_api_key"
        ```
    *   **macOS/Linux:**
        ```bash
        export OPENAI_API_KEY="your_api_key"
        ```
        (You might want to add this to your `.bashrc` or `.zshrc` file to make it permanent.)

2.  **Modify the Script:**  Change the `api_key` assignment in the script to:

    ```python
    import os

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key not found.  Please set the OPENAI_API_KEY environment variable.")
    ```

This way, the script will retrieve the API key from the environment variable, keeping it secure.

## Troubleshooting 

*   **`ValueError: OpenAI API key not found...`:**  Make sure you have set your OpenAI API key correctly, either directly in the script (for private use only) or as an environment variable (recommended).
*   **`JSONDecodeError`:** This usually indicates an issue with the OpenAI API response.  Check your OpenAI account status and API usage.  It could also be caused by unusual characters in the input text.
*   **`FileNotFoundError`:**  Ensure that the `SOURCE_DIR` and `DESTINATION_DIR` variables are set to the correct, existing paths.  Use absolute paths to avoid ambiguity.
*   **Files not being renamed:**
    *   Make sure the files in your `SOURCE_DIR` have the correct extensions (`.md`, `.markdown`, or `.pdf`).
    *   Check the console output for error messages.  The script might be skipping files if it cannot extract text or if a duplicate filename already exists.
*   **Incorrect Metadata:** The accuracy of the renaming depends on the quality of the text content and the ability of the OpenAI model to extract the metadata.  If the metadata is consistently incorrect, you may need to manually adjust the filenames.

## License 📝

This project is licensed under the MIT License - see the LICENSE file for details. 

---

Enjoy using these tools to automatically organize your Markdown and PDF files! 🤖📂🎉


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
