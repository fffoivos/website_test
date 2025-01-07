import subprocess
import os

# Create output directory
os.makedirs("/home/fivos/Desktop/extraction_tests/auto_docling_tests/test_output", exist_ok=True)

# Run docling
cmd = [
    "docling",
    "/home/fivos/Desktop/extraction_tests/sample_pdfs/paper_190.pdf",
    "--from", "pdf",
    "--to", "md",
    "--image-export-mode", "placeholder",
    "--no-ocr",
    "--num-threads", "5",
    "--device", "cpu",
    "-vv",
    "--output", "/home/fivos/Desktop/extraction_tests/auto_docling_tests/test_output"
]

process = subprocess.Popen(cmd)
print("Started docling process with PID:", process.pid)
process.wait()
