import os
import subprocess
from pathlib import Path

def convert_missing_pdfs():
    # Define paths
    pdf_dir = Path('/home/fivos/Desktop/unique_sxolika_pdf')
    md_output_dir = pdf_dir / 'md_output'
    
    # Create md_output directory if it doesn't exist
    md_output_dir.mkdir(exist_ok=True)
    
    # Get list of all PDF files
    pdf_files = [f for f in pdf_dir.glob('*.pdf')]
    
    # Process each PDF file
    for pdf_file in pdf_files:
        # Construct expected MD filename
        expected_md_file = md_output_dir / f"{pdf_file.stem}.md"
        
        # Check if MD file already exists
        if not expected_md_file.exists():
            print(f"Processing: {pdf_file.name}")
            try:
                # Construct and execute docling command
                command = [
                    'docling',
                    str(pdf_file),
                    '--no-ocr',
                    '--output',
                    str(md_output_dir)
                ]
                
                # Run without capturing output to see live progress
                result = subprocess.run(
                    command,
                    check=True  # This will raise an exception if the command fails
                )
                
                print(f"Successfully converted: {pdf_file.name}")
                    
            except subprocess.CalledProcessError as e:
                print(f"Error converting {pdf_file.name} - Command failed with return code {e.returncode}")
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {str(e)}")
        else:
            print(f"Skipping {pdf_file.name} - MD file already exists")

if __name__ == "__main__":
    convert_missing_pdfs()