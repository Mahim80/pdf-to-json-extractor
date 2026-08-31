import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import json

# পেজ সেটআপ
st.set_page_config(page_title="NID OCR Extractor", layout="wide")

st.title("🚀 Fast NID OCR Extractor")
st.write("এই টুলটি PDF থেকে ছবি তৈরি করে Tesseract OCR দিয়ে বাংলা রিড করে।")

def extract_structured_data(text_list):
    # আপনার চাওয়া JSON স্ট্রাকচার
    data = {
        "basic_info": {},
        "personal_info": {},
        "present_address": {},
        "permanent_address": {},
        "additional_info": {}
    }

    full_text = " ".join(text_list)
    
    # কী-ভ্যালু ফিল্টার (সহজ লজিক)
    lines = [line.strip() for line in text_list if line.strip()]
    
    for i, line in enumerate(lines):
        if "National ID" in line:
            data["basic_info"]["national_id"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Pin" in line:
            data["basic_info"]["pin"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Name(Bangla)" in line:
            data["personal_info"]["name_bangla"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Name(English)" in line:
            data["personal_info"]["name_english"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Father Name" in line:
            data["personal_info"]["father_name"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Mother Name" in line:
            data["personal_info"]["mother_name"] = lines[i+1] if i+1 < len(lines) else ""
        elif "Laptop ID" in line:
            data["additional_info"]["laptop_id"] = lines[i+1] if i+1 < len(lines) else ""

    return data

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('AI OCR দিয়ে বাংলা রিড করা হচ্ছে...'):
            # ১. পিডিএফ থেকে ইমেজ কনভার্ট (৩০০ DPI কোয়ালিটির জন্য)
            images = convert_from_bytes(uploaded_file.read(), dpi=300)
            
            raw_texts = []
            for img in images:
                # ২. Tesseract দিয়ে বাংলা (ben) এবং ইংলিশ (eng) পড়া
                text = pytesseract.image_to_string(img, lang='ben+eng')
                raw_texts.append(text)
            
            # ৩. ডাটা সাজানো
            structured_res = extract_structured_data(" ".join(raw_texts).split('\n'))
            
            st.success("Extraction Complete!")
            
            final_json = json.dumps(structured_res, indent=4, ensure_ascii=False)
            
            col1, col2 = st.columns(2)
            with col1:
                st.json(structured_res)
            with col2:
                st.code(final_json, language='json')
                st.download_button("Download JSON", final_json, file_name="nid_data.json")
                
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("টিপস: Manage App বাটনে ক্লিক করে Logs চেক করুন কি সমস্যা হচ্ছে।")

st.divider()
st.caption("Engine: Tesseract-OCR | Language: Bengali + English")
