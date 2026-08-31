import streamlit as st
import pdfplumber
import json
import re

st.set_page_config(page_title="NID Raw Extractor", layout="wide")

def clean_val(text):
    if text:
        # শুধুমাত্র টেকনিক্যাল গার্বেজ (নাল বাইট, ইনভিজিবল ক্যারেক্টার) রিমুভ করবে
        # কিন্তু কোনো বাংলা অক্ষর বা বানান পরিবর্তন করবে না
        text = text.replace('\u0000', '').replace('\ufeff', '')
        # অতিরিক্ত স্পেস এবং নিউলাইন ক্লিন করে এক লাইনে আনবে
        text = " ".join(text.split()).strip()
        return text
    return ""

def extract_field(text, start, end):
    try:
        # প্যাটার্ন ম্যাচিং: শুরু এবং শেষ শব্দের মাঝখানের Raw টেক্সট নিবে
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
    
    # আপনার চাওয়া স্ট্রাকচার অনুযায়ী Raw Data ম্যাপিং
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
            "name_english": extract_field(full_text, "Name(English)", "Date of Birth"),
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
            "mouza_moholla": extract_field(full_text, "Mouza/Moholla", "Additional"),
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

# UI ডিজাইন
st.title("📄 NID Raw Data Extractor")
st.warning("এই টুলটি পিডিএফ থেকে কোনো বানান সংশোধন করবে না, যা আছে ঠিক তাই দিবে।")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    data = process_nid_data(uploaded_file)
    final_json = json.dumps(data, indent=4, ensure_ascii=False)
    
    st.success("Extraction Done (No corrections applied)")
    
    st.subheader("Final JSON Response")
    st.code(final_json, language='json')
    st.download_button("Download JSON", final_json, file_name="raw_nid_data.json")
