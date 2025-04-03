import os
from pathlib import Path

"""
Some tips for you:
This is just a simple PDF reader that uses the LlamaIndex library to extract text from PDFs.
But if you have enough GPU resources, I strongly recommend using the OLM OCR model to extract text from PDFs.
It has much better performance than the other PDF reader libs. The only problem is that it is required to use high-end GPU.

- Recent NVIDIA GPU (tested on RTX 4090, L40S, A100, H100, A6000...) with at least 20 GB of GPU RAM
- Follow: https://github.com/allenai/olmocr
"""

def pdfreader(file_path:str)->str:
    assert os.path.exists(file_path), "File does not exist"
    assert file_path.endswith(".pdf"), "File format not supported"

    from llama_index.readers.file import PDFReader
    doc = PDFReader().load_data(file=Path(file_path))

    text = "\n\n".join([d.get_content() for d in doc])
    return text

def plainreader(file_path:str)->str:
    assert os.path.exists(file_path), "File does not exist"
    with open(file_path, "r") as f:
        text = f.read()
    return text