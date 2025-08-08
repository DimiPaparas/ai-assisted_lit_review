# -*- coding: utf-8 -*-
"""
A script that integrates BibTeX parsing with the Gemini API. It reads PDFs 
from a folder, finds their corresponding BibTeX citekey, generates a summary 
using Gemini, saves the summary with the citekey, and archives the file.
"""
import os
import shutil
import sys
import time
import bibtexparser
import google.generativeai as genai

# --- CONFIGURATION ---
# 1. Directory and File Paths
PAPERS_TO_READ_DIR = "papers_to_read"
READ_PAPERS_DIR = "read_papers"

# The BibTeX file to search for citekeys
BIBTEX_FILE_PATH = "references.bib" 

MASTER_PROMPT_FILE = "assets/master_prompt.txt"
# Optional reference manual for the prompt
SIUNITX_MANUAL = "assets/siunitx.pdf" 

SUMMARIES_FILE = "paper_summaries.txt"

# 2. Gemini API Configuration
# Option 1 (Recommended): Use an environment variable named "GEMINI_API_KEY".
# The script will prioritize this method if the environment variable is found.
# How to set: export GEMINI_API_KEY='your_key_here'

# Option 2: Paste your API key directly below.
# IMPORTANT: Be careful not to share this file publicly if you paste your key here.
API_KEY_PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE"

# --- DO NOT EDIT BELOW THIS LINE ---

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    print("-> Configured Gemini API with key from environment variable.")
elif API_KEY_PLACEHOLDER != "PASTE_YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=API_KEY_PLACEHOLDER)
    print("-> Configured Gemini API with key from the script file.")
else:
    print("\nERROR: Gemini API key not found.")
    print("Please do one of the following:")
    print("  1. Paste your API key into the 'API_KEY_PLACEHOLDER' variable in this script.")
    print("  2. Set the 'GEMINI_API_KEY' environment variable (recommended).")
    sys.exit(1)

# We will use 'gemini-2.5-pro' as it's excellent for multi-modal tasks.
MODEL = 'gemini-2.5-pro'
# --- END OF CONFIGURATION ---


def parse_file_path_from_entry(file_field_string):
    """
    Parses the file path from a Zotero/Mendeley-style 'file' field.
    Example format: ':path/to/my/file.pdf:PDF'
    """
    if not file_field_string:
        return None
    parts = file_field_string.split(';')
    for part in parts:
        # Check for PDF or HTML files, case-insensitively
        if '.pdf' in part.lower() or '.html' in part.lower():
            path_segments = part.split(':')
            # Iterate backwards to find the last segment that is a file
            for segment in reversed(path_segments):
                if segment.lower().endswith(('.pdf', '.html')):
                    return segment
    return None

def create_pdf_to_citekey_map(bib_database):
    """
    Creates a dictionary mapping PDF filenames to their BibTeX citekeys.
    
    Returns:
        dict: A mapping like {'hayes2002.pdf': 'hayes2002distributed'}
    """
    mapping = {}
    for entry in bib_database.entries:
        citekey = entry.get('ID')
        file_field = entry.get('file')
        
        if not citekey or not file_field:
            continue
            
        pdf_path = parse_file_path_from_entry(file_field)
        if pdf_path:
            # Extract just the filename from the full path
            pdf_filename = os.path.basename(pdf_path)
            mapping[pdf_filename] = citekey
    
    if not mapping:
        print("  - WARNING: No valid 'file' entries found in the BibTeX file. The script may not find citekeys.")
        
    return mapping

def setup_directories():
    """Ensures that the necessary directories exist."""
    os.makedirs(PAPERS_TO_READ_DIR, exist_ok=True)
    os.makedirs(READ_PAPERS_DIR, exist_ok=True)
    os.makedirs("assets", exist_ok=True)
    print("-> Directories are set up.")

def main():
    """Main function to run the PDF processing pipeline."""
    print("--- Integrated BibTeX and Gemini Pipeline Initialized ---")

    setup_directories()

    # --- Load Master Prompt ---
    try:
        with open(MASTER_PROMPT_FILE, 'r', encoding='utf-8') as f:
            master_prompt = f.read()
        print(f"-> Successfully loaded master prompt from '{MASTER_PROMPT_FILE}'.")
    except FileNotFoundError:
        print(f"\nERROR: Master prompt file not found at '{MASTER_PROMPT_FILE}'.")
        print("Please create this file in the 'assets' directory. Exiting.")
        return

    # --- Load BibTeX file and create the lookup map ---
    try:
        with open(BIBTEX_FILE_PATH, 'r', encoding='utf-8') as bibfile:
            bib_database = bibtexparser.load(bibfile)
        pdf_citekey_map = create_pdf_to_citekey_map(bib_database)
    except FileNotFoundError:
        print(f"\nERROR: BibTeX file not found at '{BIBTEX_FILE_PATH}'.")
        print("Please place your .bib file in the root directory and update the path in the script. Exiting.")
        return
    except Exception as e:
        print(f"\nERROR: Failed to parse BibTeX file. Details: {e}. Exiting.")
        return

    # --- Upload Reference Manual (Optional) ---
    siunitx_manual_file = None
    try:
        if os.path.exists(SIUNITX_MANUAL):
            print("\n  - Uploading reference manual to Gemini...")
            siunitx_manual_file = genai.upload_file(path=SIUNITX_MANUAL, display_name=os.path.basename(SIUNITX_MANUAL))
            print(f"  - Upload successful! File URI: {siunitx_manual_file.uri}")
        else:
            print(f"\nINFO: Optional reference manual '{SIUNITX_MANUAL}' not found. Proceeding without it.")
    except Exception as e:
        print(f"\nWARNING: Could not upload reference manual. Details: {e}. Proceeding without it.")
        siunitx_manual_file = None

    # --- Find PDFs to Process ---
    try:
        pdf_files = [f for f in os.listdir(PAPERS_TO_READ_DIR) if f.lower().endswith(('.pdf', '.html'))]
    except FileNotFoundError:
        print(f"\nERROR: The directory '{PAPERS_TO_READ_DIR}' does not exist. Exiting.")
        return

    if not pdf_files:
        print("\nNo new papers found in the 'papers_to_read' directory. Exiting.")
        return
        
    print(f"\nFound {len(pdf_files)} file(s) to process: {', '.join(pdf_files)}")

    # --- Initialize the Model ---
    model = genai.GenerativeModel(MODEL)

    # --- Process Each PDF ---
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PAPERS_TO_READ_DIR, pdf_file)
        print(f"\n--- Processing: {pdf_file} ---")

        citekey = pdf_citekey_map.get(pdf_file, os.path.splitext(pdf_file)[0])
        if citekey == os.path.splitext(pdf_file)[0]:
            print(f"  - WARNING: Could not find citekey for '{pdf_file}' in '{BIBTEX_FILE_PATH}'. Using filename as fallback.")
        else:
             print(f"  - Found citekey: '{citekey}'")

        try:
            # 1. Upload the main paper to the Gemini API
            print("  - Uploading paper to Gemini...")
            uploaded_file = genai.upload_file(path=pdf_path, display_name=pdf_file)
            print(f"  - Upload successful! File URI: {uploaded_file.uri}")

            # 2. Construct the prompt and generate content
            print("  - Generating summary...")
            prompt_parts = [master_prompt]
            if siunitx_manual_file:
                prompt_parts.append(siunitx_manual_file)
            prompt_parts.append(uploaded_file)
            
            response = model.generate_content(prompt_parts, request_options={'timeout': 600})

            # 3. Append the summary to the output file
            print("  - Saving summary...")
            with open(SUMMARIES_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\\section*{{{citekey}}}\n\n") # Using section* for un-numbered sections
                f.write(response.text)
                f.write("\n\n---\n\n") # Separator for clarity
            
            print(f"  - Summary for '{citekey}' appended to '{SUMMARIES_FILE}'.")

            # 4. Move the processed PDF to the archive directory
            print("  - Archiving processed file...")
            destination_path = os.path.join(READ_PAPERS_DIR, pdf_file)
            shutil.move(pdf_path, destination_path)
            print(f"  - Moved '{pdf_file}' to '{READ_PAPERS_DIR}'.")

            # 5. Clean up the uploaded paper from the API service
            print("  - Deleting uploaded paper from service...")
            genai.delete_file(uploaded_file.name)

        except Exception as e:
            print(f"\n  - ERROR: An error occurred while processing {pdf_file}: {e}")
            print("  - Skipping this file and moving to the next one.")
            continue
        
        # A small delay to respect API rate limits
        time.sleep(2)
        
    # Clean up the reference manual at the end if it was uploaded
    if siunitx_manual_file:
        print("\n  - Deleting uploaded reference manual from service...")
        genai.delete_file(siunitx_manual_file.name)

    print("\n--- Pipeline Finished ---")

if __name__ == "__main__":
    main()
