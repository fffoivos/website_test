import fitz  # PyMuPDF

def extract_pdf_content(pdf_path):
    content = ""
    doc = fitz.open(pdf_path)
    
    # Define the rectangles for content extraction (adjust these values as needed)
    # Format: (left, top, right, bottom)
    content_rects = [
        fitz.Rect(50, 50, 550, 700),  # Main content area
        fitz.Rect(50, 700, 550, 750)  # Additional content area if needed
    ]
    
    # Define rectangles for areas to exclude (like headers and footers)
    exclude_rects = [
        fitz.Rect(0, 0, 595, 50),    # Top of page (header)
        fitz.Rect(0, 750, 595, 842)  # Bottom of page (footer)
    ]
    
    # Skip first two pages
    for page_num in range(2, len(doc)):
        page = doc[page_num]
        
        page_content = ""
        
        # Extract text from specified content rectangles
        for rect in content_rects:
            page_content += page.get_text("text", clip=rect)
        
        # Remove text from exclude rectangles
        for rect in exclude_rects:
            exclude_text = page.get_text("text", clip=rect)
            page_content = page_content.replace(exclude_text, "")
        
        content += page_content.strip() + "\n\n"  # Add extra newlines between pages
    
    doc.close()
    return content


# Usage
pdf_path = '/home/fivos/Downloads/_Όνειρα.pdf'
extracted_text = extract_pdf_content(pdf_path)

# Write to txt file
with open('pdf_2_text.txt', 'w', encoding='utf-8') as out_file:
    out_file.write(extracted_text)