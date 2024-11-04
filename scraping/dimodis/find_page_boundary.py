import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz
import os

class PDFRegionSelector:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF Region Selector")
        
        self.pdf_folder = None
        self.image = None
        self.rect_start = None
        self.rect_end = None
        self.rectangles = []
        self.doc = None
        
        self.canvas = tk.Canvas(self.master)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.load_button = tk.Button(self.master, text="Select PDF Folder", command=self.select_folder)
        self.load_button.pack()
        
        self.extract_button = tk.Button(self.master, text="Extract Text from All PDFs", command=self.extract_text_all)
        self.extract_button.pack()

    def select_folder(self):
        self.pdf_folder = filedialog.askdirectory()
        if self.pdf_folder:
            pdf_files = [f for f in os.listdir(self.pdf_folder) if f.endswith('.pdf')]
            if pdf_files:
                self.load_pdf(os.path.join(self.pdf_folder, pdf_files[0]))
            else:
                print("No PDF files found in the selected folder.")

    def load_pdf(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        if len(self.doc) >= 4:
            page = self.doc.load_page(3)  # Load 4th page (index 3)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.image = ImageTk.PhotoImage(image=img)
            self.canvas.config(width=pix.width, height=pix.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)
        else:
            print("The PDF does not have a 4th page.")

    def on_press(self, event):
        self.rect_start = (event.x, event.y)

    def on_drag(self, event):
        if self.rect_start:
            self.canvas.delete("rect")
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1], 
                                         event.x, event.y, outline="red", tags="rect")

    def on_release(self, event):
        if self.rect_start:
            self.rect_end = (event.x, event.y)
            self.rectangles.append((self.rect_start[0], self.rect_start[1], 
                                    self.rect_end[0], self.rect_end[1]))
            self.rect_start = None
            self.rect_end = None

    def extract_text_all(self):
        if not self.pdf_folder or not self.rectangles:
            print("Please select a PDF folder and define at least one region.")
            return
        
        output_folder = os.path.join(self.pdf_folder, "extracted_texts")
        os.makedirs(output_folder, exist_ok=True)

        for pdf_file in os.listdir(self.pdf_folder):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, pdf_file)
                doc = fitz.open(pdf_path)
                extracted_text = ""
                
                for page_num in range(2, len(doc)):  # Start from the 3rd page (index 2)
                    page = doc[page_num]
                    
                    extracted_text += f"\n\n{'='*20}\nPAGE {page_num + 1}\n{'='*20}\n\n"
                    
                    for rect in self.rectangles:
                        r = fitz.Rect(rect)
                        blocks = page.get_text("dict", clip=r)["blocks"]
                        for b in blocks:
                            if "lines" in b:
                                for l in b["lines"]:
                                    for s in l["spans"]:
                                        extracted_text += s["text"]
                                    extracted_text += "\n"
                            extracted_text += "\n"
                
                output_path = os.path.join(output_folder, f"{os.path.splitext(pdf_file)[0]}.txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                
                print(f"Extracted text saved to {output_path}")
                doc.close()

root = tk.Tk()
app = PDFRegionSelector(root)
root.mainloop()