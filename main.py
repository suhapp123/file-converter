from flask import Flask, render_template, request, send_file
import os
import pymupdf as fitz
from pdf2image import convert_from_path
from docx import Document
from reportlab.pdfgen import canvas
from PIL import Image
import threading
import time
import pypandoc

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        file = request.files['file']
        conversion = request.form['conversion']
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        output_path = ""

        if conversion == "pdf_to_word":
            doc = fitz.open(filepath)
            text = "\n".join([page.get_text() for page in doc])
            docx_file = os.path.join(CONVERTED_FOLDER, filename.replace('.pdf', '.docx'))
            document = Document()
            document.add_paragraph(text)
            document.save(docx_file)
            output_path = docx_file

        elif conversion == "word_to_pdf":
            pdf_path = os.path.join(CONVERTED_FOLDER, filename.replace('.docx', '.pdf'))
            try:
                pypandoc.convert_file(filepath, 'pdf', outputfile=pdf_path)
                output_path = pdf_path
            except Exception as e:
                return f"Conversion failed: {str(e)}"

        elif conversion == "txt_to_pdf":
            pdf_path = os.path.join(CONVERTED_FOLDER, filename.replace('.txt', '.pdf'))
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            c = canvas.Canvas(pdf_path)
            y = 800
            for line in lines:
                if line.strip():
                    c.drawString(50, y, line.strip()[:80])
                    y -= 20
                    if y < 50:
                        c.showPage()
                        y = 800
            c.save()
            output_path = pdf_path

        elif conversion == "image_to_pdf":
            image = Image.open(filepath)
            pdf_path = os.path.join(CONVERTED_FOLDER, filename.rsplit('.', 1)[0] + '.pdf')
            image.convert('RGB').save(pdf_path)
            output_path = pdf_path

        elif conversion == "pdf_to_image":
            images = convert_from_path(filepath)
            image_path = os.path.join(CONVERTED_FOLDER, filename.replace('.pdf', '.png'))
            images[0].save(image_path, 'PNG')
            output_path = image_path

        else:
            return "Conversion type not supported."

        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return "Conversion failed. Please try again."
    
    except Exception as e:
        return f"Error during conversion: {str(e)}"

# Auto-delete files older than 1 minute
AGE_LIMIT = 60

def clean_old_files(folder, age_limit):
    print(f"Started cleanup thread for: {folder}")
    while True:
        now = time.time()
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > age_limit:
                    try:
                        os.remove(filepath)
                        print(f"[DELETED] {filepath}")
                    except Exception as e:
                        print(f"[ERROR] Cannot delete {filepath}: {e}")
        time.sleep(30)

threading.Thread(target=clean_old_files, args=(UPLOAD_FOLDER, AGE_LIMIT), daemon=True).start()
threading.Thread(target=clean_old_files, args=(CONVERTED_FOLDER, AGE_LIMIT), daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)


