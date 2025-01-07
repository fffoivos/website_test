import time
from auto_docling import is_docling_running
import subprocess
import os
import sys

# Add parent directory to Python path to import auto_docling
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_docling_detection():
    # Test 1: When no docling is running
    print("Test 1: Checking when no docling is running...")
    result = is_docling_running()
    print(f"Docling running: {result}")
    assert result == False, "Test failed: Detected docling when none should be running"
    
    # Create test output directory
    os.makedirs("/home/fivos/Desktop/extraction_tests/auto_docling_tests/test_output", exist_ok=True)
    
    # Test 2: Start docling and check detection
    print("\nTest 2: Starting docling and checking detection...")
    cmd = [
        "/usr/bin/python3",
        "/home/fivos/.local/bin/docling",
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
    
    # Start docling
    process = subprocess.Popen(cmd)
    print("Started docling process")
    
    # Wait a bit for process to start
    time.sleep(2)
    
    # Check if docling is detected
    result = is_docling_running()
    print(f"Docling running: {result}")
    assert result == True, "Test failed: Could not detect running docling process"
    
    # Wait for process to finish
    process.wait()
    
    # Test 3: Check after docling finished
    print("\nTest 3: Checking after docling finished...")
    result = is_docling_running()
    print(f"Docling running: {result}")
    assert result == False, "Test failed: Detected docling when process should have finished"
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_docling_detection()
