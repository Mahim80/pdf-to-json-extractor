import streamlit as st
import pdfplumber
import json
import re

st.set_page_config(page_title="NID Master Extractor (Fixed)", layout="wide")

def fix_bangla_typos(text):
    if not text: return ""
    
    # ১. কমন এনকোডিং এরর কারেকশন (ফন্ট ভাঙা সমস্যা)
    corrections = {
        "মাঃ": "মোঃ",
        "মাছাঃ": "মোছাঃ",
        "শিরফল": "শরিফুল",
        "আকিলমা": "আকলিমা",
        "বগম": "বেগম",
        "সাতীরা": "সাতক্ষীরা",
        "খলনা": "খুলনা",
        "দবহাটা": "দেবহাটা",
        "কিলয়া": "কুলিয়া",
        "শ্রিমক": "শ্রমিক",
        "িহজলডাাংগা": "হিজলডাঙ্গা",
        "িহজলডাা": "হিজলডাঙ্গা",
        "৪থ": "৪র্থ",
        "৫ম": "৫ম",
        "জাসনা": "জোসনা",
        "আার": "আক্তার",
        "আাতা": "আক্তার",
        "সা তক্ষী রা": "সাতক্ষীরা",
        "ঠারগাঁও": "ঠাকুরগাঁও",
        "মাঃ": "মোঃ",
        "চতু": "চেতু",
        "বগম": "বেগম"
    }
    
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    
    # ২. সাইডবার থেকে আসা অপ্রয়োজনীয় টেক্সট রিমুভ (Garbage Filter)
    garbage_words = [
        "VOTER FORM", "Smart Card Info", "License Documents", 
        "OTHER", "No Documents Available", "SEARCH", "Citizen"
    ]
    for word in garbage_words:
        text = text.replace(word, "")
        
    return text.strip()

def clean_val(text):
    if text:
        text = text.replace('\u0000', '').replace('\ufeff', '')
        # অতিরিক্ত স্পেস এবং নিউলাইন ক্লিন
        text = " ".join(text.split()).strip()
        return fix_bangla_typos(text)
    return ""

def extract_field(text, start, end):
    try:
        # Regex প্যাটার্ন যা শুরু এবং শেষ দেখে মাঝখানের ডাটা নিবে
        pattern = re.escape(start) + r"(.*?)" + re.escape(end)
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return clean_val(match.group(1))
    except:
        pass
    return ""

def process_nid_data(pdf_file):
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    # PHP লজিক অনুযায়ী ফিল্ড এক্সট্রাকশন
    res = {
        "basic_info": {
            "national_id": extract_field(full_text, "National ID", "Pin"),
            "pin": extract_field(full_text, "Pin", "Status"),
            "status": extract_field(full_text, "Status", "Afis Status") or extract_field(full_text, "Status", "Lock"),
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
            "marital": extract_field(full_text, "Marital", "Occupation"),
            "occupation": extract_field(full_text, "Occupation", "Disability"),
            "religion": extract_field(full_text, "Religion", "Religion Other") or extract_field(full_text, "Religion", "Death")
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
            "voter_area": extract_field(full_text, "Voter Area", "Voter At"),
            "voter_at": extract_field(full_text, "Voter At", "\n")
        }
    }
    
    return res

# UI Design
st.title("📄 NID Extractor (Fixed Engine)")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    data = process_nid_data(uploaded_file)
    final_json = json.dumps(data, indent=4, ensure_ascii=False)
    
    st.success("Data Extracted & Fixed!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Tree")
        st.json(data)
    with col2:
        st.subheader("Final JSON")
        st.code(final_json, language='json')
        st.download_button("Download JSON", final_json, file_name="nid_fixed.json")
