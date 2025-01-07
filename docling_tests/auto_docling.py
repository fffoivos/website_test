import os
import time
import shutil
import subprocess
from pathlib import Path
import re

# Define paths
OUTPUT_DIR = "/home/fivos/Desktop/extraction_tests/ypologistis_mou_output"
SOURCE_DIR = "/home/fivos/Desktop/extraction_tests/ypologistis_moy"
PROCESSED_DIR = "/home/fivos/Desktop/extraction_tests/processed_from_ypologistis_moy"
PROBLEMATIC_DIR = "/home/fivos/Desktop/extraction_tests/problematic_pdfs"
LOG_FILE = "/home/fivos/Desktop/extraction_tests/docling.log"

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(PROBLEMATIC_DIR, exist_ok=True)

def is_docling_running():
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        return any('/usr/bin/python3 /home/fivos/.local/bin/docling' in line for line in result.stdout.splitlines())
    except subprocess.CalledProcessError:
        return False

def move_processed_files():
    # Get list of successfully converted files (md files)
    md_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
    moved_count = 0
    
    for md_file in md_files:
        # Get the base name without extension
        base_name = os.path.splitext(md_file)[0]
        pdf_file = f"{base_name}.pdf"
        source_path = os.path.join(SOURCE_DIR, pdf_file)
        dest_path = os.path.join(PROCESSED_DIR, pdf_file)
        
        if os.path.exists(source_path):
            shutil.move(source_path, dest_path)
            moved_count += 1
            print(f"Moved: {pdf_file}")
    
    print(f"\nTotal files moved: {moved_count}")
    return moved_count

def handle_crash():
    """Check log for last processed PDF and move it to problematic folder"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            log_content = f.read()
            
        # Find all "Processing document" lines
        matches = re.findall(r"Processing document (.+?\.pdf)", log_content)
        if matches:
            # Get the last PDF that was being processed
            problematic_pdf = matches[-1]
            source_path = os.path.join(SOURCE_DIR, problematic_pdf)
            if os.path.exists(source_path):
                dest_path = os.path.join(PROBLEMATIC_DIR, problematic_pdf)
                shutil.move(source_path, dest_path)
                print(f"Moved problematic file {problematic_pdf} to {PROBLEMATIC_DIR}")

def start_docling():
    cmd = [
        "docling",
        SOURCE_DIR,
        "--from", "pdf",
        "--to", "md",
        "--image-export-mode", "placeholder",
        "--no-ocr",
        "--num-threads", "5",
        "--device", "cpu",
        "-vv",
        "--output", OUTPUT_DIR
    ]
    
    # Open log file and start docling with output redirection
    with open(LOG_FILE, 'w') as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        print("Started docling process with PID:", process.pid)
        return process

def main():
    while True:
        print("\nChecking docling status...")
        if not is_docling_running():
            print("Docling is not running")
            # Check if it crashed and handle problematic PDF
            handle_crash()
            
            # Move any processed files
            moved = move_processed_files()
            
            # Check if there are any PDF files left to process
            remaining_pdfs = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.pdf')]
            if remaining_pdfs:
                print(f"Found {len(remaining_pdfs)} files to process. Starting docling...")
                process = start_docling()
            else:
                print("No more PDF files to process. Exiting.")
                break
        else:
            print("Docling is still running")
        
        # Wait 10 minutes
        print("Waiting 1 minutes before next check...")
        time.sleep(60)

if __name__ == "__main__":
    main()
