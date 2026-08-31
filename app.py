import streamlit as st
import fitz  # PyMuPDF
import easyocr
import numpy as np
from PIL import Image
import json
import re

# পেজ কনফিগারেশন
st.set_page_config(page_title="NID OCR Extractor", layout="wide")

# OCR মডেল লোড করা (Bengali এবং English)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bn', 'en'])

reader = load_ocr()

def clean_text(text):
    return " ".join(text.split()).strip()

def process_pdf_to_ocr(pdf_file):
    # ১. পিডিএফ থেকে ইমেজ তৈরি করা
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    all_ocr_text = []

    progress_bar = st.progress(0)
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # হাই রেজোলিউশন
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # ২. ইমেজ থেকে OCR করা
        img_np = np.array(img)
        result = reader.readtext(img_np, detail=0) # শুধু টেক্সট নিবে
        all_ocr_text.extend(result)
        
        progress_bar.progress((page_num + 1) / len(pdf_document))

    return all_ocr_text

def parse_ocr_to_json(text_list):
    # OCR থেকে পাওয়া টেক্সট লিস্টকে স্ট্রাকচারে সাজানো
    data = {
        "basic_info": {},
        "personal_info": {},
        "present_address": {},
        "permanent_address": {},
        "additional_info": {}
    }

    # সব টেক্সট এক লাইনে নিয়ে আসা সহজ খোঁজার জন্য
    full_content = " ".join(text_list)
    
    # কী-ভ্যালু খোঁজার লজিক
    keys_map = {
        "national_id": "National ID",
        "pin": "Pin",
        "name_bangla": "Name(Bangla)",
        "name_english": "Name(English)",
        "father_name": "Father Name",
        "mother_name": "Mother Name",
        "date_of_birth": "Date of Birth",
        "voter_no": "Voter No",
        "laptop_id": "Laptop ID",
        "voter_area": "Voter Area"
    }

    # টেক্সট লিস্টের মাধ্যমে ডাটা ফিলআপ করা
    for i, val in enumerate(text_list):
        clean_val = val.strip()
        
        # Basic & Personal Info
        if "National ID" in clean_val:
            data["basic_info"]["national_id"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Pin" in clean_val:
            data["basic_info"]["pin"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Name(Bangla)" in clean_val:
            data["personal_info"]["name_bangla"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Name(English)" in clean_val:
            data["personal_info"]["name_english"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Father Name" in clean_val:
            data["personal_info"]["father_name"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Mother Name" in clean_val:
            data["personal_info"]["mother_name"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Date of Birth" in clean_val:
            data["personal_info"]["date_of_birth"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Laptop ID" in clean_val:
            data["additional_info"]["laptop_id"] = text_list[i+1] if i+1 < len(text_list) else ""
        elif "Voter Area" in clean_val:
            data["additional_info"]["voter_area"] = text_list[i+1] if i+1 < len(text_list) else ""

    return data

# UI
st.title("🚀 AI Powered NID OCR Extractor")
st.write("এই পদ্ধতিতে PDF প্রথমে ছবিতে রূপান্তর হয় এবং AI দিয়ে বাংলা পড়া হয়। ফলে বানান সঠিক থাকে।")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    with st.spinner('AI মডেল কাজ করছে... প্রথমবার কিছুটা সময় নিতে পারে।'):
        # OCR প্রসেস
        raw_text_list = process_pdf_to_ocr(uploaded_file)
        
        # স্ট্রাকচারড ডাটা তৈরি
        structured_data = parse_ocr_to_json(raw_text_list)
        
        final_json = json.dumps(structured_data, indent=4, ensure_ascii=False)
        
        st.success("Extraction Done with AI OCR!")
        
        tab1, tab2, tab3 = st.tabs(["📊 Structure View", "💻 Raw JSON", "📝 OCR Raw Text"])
        
        with tab1:
            st.json(structured_data)
        
        with tab2:
            st.code(final_json, language='json')
            st.download_button("Download JSON", final_json, file_name="nid_ocr_data.json")
            
        with tab3:
            st.write(raw_text_list)

st.divider()
st.caption("EasyOCR Engine | Bengali & English Support")
