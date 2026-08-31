import streamlit as st
import pdfplumber
import json
import re

# পেজ সেটআপ
st.set_page_config(page_title="NID Master Extractor (PHP Logic)", layout="wide")

def clean_val(text):
    if text:
        # এনকোডিং এরর এবং অতিরিক্ত স্পেস ক্লিন করা
        text = text.replace('\u0000', '').replace('\ufeff', '')
        # মোঃ এবং মোছাঃ কারেকশন (আপনার আগের সমস্যা সমাধান)
        text = text.replace("মাঃ", "মোঃ").replace("মাছাঃ", "মোছাঃ")
        return " ".join(text.split()).strip()
    return ""

def extract_field(text, start, end):
    # PHP-র extractField ফাংশনের পাইথন ভার্সন
    try:
        pattern = re.escape(start) + r"(.*?)" + re.escape(end)
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return clean_val(match.group(1))
    except:
        pass
    return ""

def process_nid_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
        
    # PHP কোডের মতো ডেটা ম্যাপিং
    res = {
        "basic_info": {
            "national_id": extract_field(full_text, "National ID", "Pin"),
            "pin": extract_field(full_text, "Pin", "Status"),
            "status": extract_field(full_text, "Status", "Afis Status") or extract_field(full_text, "Status", "checked"),
            "voter_no": extract_field(full_text, "Voter No", "Form No"),
            "form_no": extract_field(full_text, "Form No", "Sl No"),
            "tag": extract_field(full_text, "Tag", "Name(Bangla)")
        },
        "personal_info": {
            "name_bangla": extract_field(full_text, "Name(Bangla)", "Name(English)"),
            "name_english": extract_field(full_text, "Name(English)", "Date of Birth").upper(),
            "date_of_birth": extract_field(full_text, "Date of Birth", "Birth Place"),
            "birth_place": extract_field(full_text, "Birth Place", "Birth Other"),
            "father_name": extract_field(full_text, "Father Name", "Mother Name"),
            "mother_name": extract_field(full_text, "Mother Name", "Spouse Name"),
            "gender": extract_field(full_text, "Gender", "Marital"),
            "occupation": extract_field(full_text, "Occupation", "Disability"),
            "religion": extract_field(full_text, "Religion", "Religion Other") or extract_field(full_text, "Religion", "\n")
        },
        "present_address": {
            "division": extract_field(full_text, "Present Address Division", "District"),
            "district": extract_field(full_text, "District", "RMO"),
            "upozila": extract_field(full_text, "Upozila", "Union/Ward"),
            "union_ward": extract_field(full_text, "Union/Ward", "Mouza/Moholla"),
            "post_office": extract_field(full_text, "Post Office", "Postal Code"),
            "postal_code": extract_field(full_text, "Postal Code", "Region")
        },
        "additional_info": {
            "laptop_id": extract_field(full_text, "Laptop ID", "NID Father"),
            "nid_father": extract_field(full_text, "NID Father", "NID Mother"),
            "nid_mother": extract_field(full_text, "NID Mother", "Nid Spouse"),
            "voter_area": extract_field(full_text, "Voter Area", "Voter At")
        }
    }
    
    return res

# UI ডিজাইন
st.title("📄 NID Extractor (Regex Engine)")
st.info("আপনার PHP কোডের লজিক অনুযায়ী ডেটা ক্যাটাগরি করা হয়েছে।")

uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])

if uploaded_file is not None:
    data = process_nid_data(uploaded_file)
    
    # JSON Response
    final_json = json.dumps(data, indent=4, ensure_ascii=False)
    
    tab1, tab2 = st.tabs(["📊 Structure View", "💻 Raw JSON"])
    
    with tab1:
        st.json(data)
    
    with tab2:
        st.code(final_json, language='json')
        st.download_button("Download JSON", final_json, file_name="nid_data.json")

st.divider()
st.caption("Developer: Python Implementation of PHP Parser Logic")
