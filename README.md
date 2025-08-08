# AI-Assisted Literature Review
(a.k.a. Gemini PDF Summarizer with BibTeX Integration)

This script automates the process of reading academic papers, generating concise summaries using the Google Gemini API, and organizing your files. It intelligently links your PDF files to your BibTeX library to use correct citation keys.

## Features
- Automatic PDF Discovery: Scans a designated folder for new PDF or HTML papers to process.

- BibTeX Integration: Parses your .bib file to find the correct citekey for each paper, ensuring consistent referencing.

- AI-Powered Summaries: Uses the powerful gemini-1.5-pro model to generate high-quality summaries based on a custom prompt.

- Context-Aware Prompts: Can include an optional reference document (e.g., a style guide or manual) in the prompt to Gemini for more tailored results.

- File Archiving: Automatically moves processed papers to an archive folder to keep your reading list clean.

- Secure API Key Handling: Prioritizes using an environment variable for your API key, with a fallback to a placeholder in the script for ease of use.

## File Structure
Before you begin, your project folder should be organized as follows:

```
.
├── main.py                 # The main Python script
├── requirements.txt        # Python dependencies
├── references.bib          # Your master BibTeX file
├── paper_summaries.txt     # The output file with all summaries (will be created)
|
├── papers_to_read/         # Place new PDFs/HTML files you want to summarize here
│   └── example_paper_1.pdf
│
├── read_papers/            # Processed papers will be moved here automatically
│
└── assets/                 # For prompt files and reference documents
    ├── master_prompt.txt   # Your custom instructions for Gemini
    └── siunitx.pdf         # (Optional) A reference PDF for the prompt
```

## Setup and Installation
### Prerequisites
- Python 3.7 or newer.
- A Google Gemini API key. You can get one from Google AI Studio.

### Install Dependencies
In your terminal, navigate to the project directory and run:
```
pip install -r requirements.txt
```

### Configure API Key
You have two options to provide your Gemini API key:

#### (Recommended) Set an environment variable. This is more secure as it keeps your key out of the source code.

On macOS/Linux: export GEMINI_API_KEY='YOUR_API_KEY_HERE'

On Windows: set GEMINI_API_KEY='YOUR_API_KEY_HERE'

#### (Easy Method) Open main.py and paste your key directly into the API_KEY_PLACEHOLDER variable.

```
API_KEY_PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE"
```
### Prepare Your Files

- BibTeX File: Place your master .bib file (e.g., references.bib) in the root directory. Make sure the file field for your entries points to the correct PDF filenames. The script uses this to match some_paper.pdf to its citekey.

- Master Prompt: Create a file named master_prompt.txt inside the assets folder. Write the instructions you want to give Gemini for summarizing the papers. Be as specific as possible.

- Papers: Add the PDF or HTML files you want to process into the papers_to_read folder.

### Usage
Once everything is set up, simply run the script from your terminal:
```
python main.py
```

The script will then:

1. Find all papers in the papers_to_read directory.
2. Look up their citekeys from references.bib.
3. For each paper, upload it to Gemini and generate a summary based on your master_prompt.txt.
4. Append the summary, tagged with its citekey, to paper_summaries.txt.
5. Move the processed paper to the read_papers folder.
6. Print its progress to the console.