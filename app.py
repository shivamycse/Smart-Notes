from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from transformers import pipeline
from docx import Document
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
summarizer = pipeline("summarization")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files and 'url' not in request.form:
        return jsonify({'error': 'No file or URL part found'})

    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        try:
            filename = secure_filename(file.filename)
            file.save(filename)
            text = extract_text(filename)
            notes = summarize_text(text)
            return jsonify({'notes': notes})
        except Exception as e:
            return jsonify({'error': str(e)})

    if 'url' in request.form:
        url = request.form['url']
        try:
            text = extract_text_from_web(url)
            notes = summarize_text(text)
            return jsonify({'notes': notes})
        except Exception as e:
            return jsonify({'error': str(e)})

    return jsonify({'error': 'File upload or URL processing failed'})

def extract_text(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    if extension == 'pdf':
        return extract_text_from_pdf(filename)
    elif extension == 'docx':
        return extract_text_from_docx(filename)
    else:
        raise Exception(f'Unsupported file format: {extension}')

def extract_text_from_pdf(pdf_path):
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        raise Exception(f'Error extracting PDF: {str(e)}')

def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        raise Exception(f'Error extracting DOCX: {str(e)}')

def extract_text_from_web(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs])
        return text
    except Exception as e:
        raise Exception(f'Error extracting web content: {str(e)}')

def summarize_text(text):
    try:
        max_chunk = 1000  # You can adjust this based on your model's max input length
        chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
        summaries = []
        for chunk in chunks:
            if len(chunk.strip()) > 0:  # Check if chunk is not empty
                summary = summarizer(chunk, max_length=min(len(chunk), 53), min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
        return '\n'.join(summaries)
    except Exception as e:
        raise Exception(f'Summarization error: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)

