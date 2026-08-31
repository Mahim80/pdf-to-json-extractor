import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import json
import re

# পেজ সেটআপ
st.set_page_config(page_title="AI NID OCR Master", layout="wide")

st.title("📄 AI NID OCR Master Extractor")
st.write("এই ভার্সনটি OCR থেকে পাওয়া এলোমেলো টেক্সটগুলোকে বুদ্ধিমানভাবে সাজিয়ে JSON তৈরি করে।")

def smart_extract(full_text):
    data = {
        "basic_info": {},
        "personal_info": {},
        "present_address": {},
        "permanent_address": {},
        "additional_info": {}
    }

    # ১. কমন ফিল্ডগুলো বের করার জন্য হেল্পার ফাংশন
    def get_val(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            # অতিরিক্ত স্পেস এবং নিউলাইন ক্লিন করা
            return " ".join(match.group(1).split()).strip()
        return ""

    # ২. Regex প্যাটার্ন (পিডিএফ-এর সিরিয়াল অনুযায়ী)
    # এই প্যাটার্নগুলো OCR-এর টেক্সট থেকে ডেটা খুঁজে নিবে
    
    # Basic Info
    data["basic_info"]["national_id"] = get_val(r"National ID\s*(\d+)", full_text)
    data["basic_info"]["pin"] = get_val(r"Pin\s*(\d+)", full_text)
    data["basic_info"]["status"] = get_val(r"Status\s*([a-zA-Z]+)", full_text)
    data["basic_info"]["voter_no"] = get_val(r"Voter No\s*(\d+)", full_text)

    # Personal Info
    # বাংলা নাম খোঁজার জন্য (Name(Bangla) এবং Name(English) এর মাঝখানের অংশ)
    data["personal_info"]["name_bangla"] = get_val(r"Name\(Bangla\)\s*(.*?)\s*Name\(English\)", full_text)
    data["personal_info"]["name_english"] = get_val(r"Name\(English\)\s*(.*?)\s*Date of Birth", full_text)
    data["personal_info"]["father_name"] = get_val(r"Father Name\s*(.*?)\s*Mother Name", full_text)
    data["personal_info"]["mother_name"] = get_val(r"Mother Name\s*(.*?)\s*Spouse Name", full_text)
    data["personal_info"]["date_of_birth"] = get_val(r"Date of Birth\s*([\d-]+)", full_text)
    data["personal_info"]["occupation"] = get_val(r"Occupation\s*(.*?)\s*Disability", full_text)

    # Address (Present)
    # অ্যাড্রেস সেকশনটি OCR-এ একটু জটিলভাবে আসে, তাই কি-ওয়ার্ড ধরে খোঁজা
    data["present_address"]["division"] = get_val(r"Present Address.*?Division\s*(\w+)", full_text)
    data["present_address"]["district"] = get_val(r"Present Address.*?District\s*(\w+)", full_text)
    data["present_address"]["upozila"] = get_val(r"Present Address.*?Upozila\s*(\w+)", full_text)
    data["present_address"]["post_office"] = get_val(r"Present Address.*?Post Office\s*(\w+)", full_text)
    data["present_address"]["postal_code"] = get_val(r"Present Address.*?Postal Code\s*(\d+)", full_text)

    # Additional Info
    data["additional_info"]["laptop_id"] = get_val(r"Laptop ID\s*([\w_]+)", full_text)
    data["additional_info"]["nid_father"] = get_val(r"NID Father\s*(\d+)", full_text)
    data["additional_info"]["nid_mother"] = get_val(r"NID Mother\s*(\d+)", full_text)
    data["additional_info"]["voter_area"] = get_val(r"Voter Area\s*(.*?)\s*Voter At", full_text)

    return data

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('AI OCR ইঞ্জিন কাজ করছে...'):
            # ১. PDF থেকে Image কনভার্ট (DPI ৩৫০ দেওয়া হয়েছে যাতে রেজাল্ট ভালো আসে)
            images = convert_from_bytes(uploaded_file.read(), dpi=350)
            
            all_text = ""
            for img in images:
                # ২. OCR দিয়ে পড়া (Bengali + English)
                text = pytesseract.image_to_string(img, lang='ben+eng')
                all_text += text + "\n"
            
            # ৩. স্মার্ট এক্সট্রাকশন
            final_data = smart_extract(all_text)
            
            st.success("Extraction Complete!")
            
            # রেজাল্ট প্রদর্শন
            final_json = json.dumps(final_data, indent=4, ensure_ascii=False)
            
            tab1, tab2, tab3 = st.tabs(["📊 Table View", "💻 JSON Output", "📝 Raw OCR Text"])
            
            with tab1:
                st.json(final_data)
            with tab2:
                st.code(final_json, language='json')
                st.download_button("Download JSON", final_json, file_name="nid_data.json")
            with tab3:
                st.text_area("OCR Raw Text (For debugging)", all_text, height=400)
                
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("Updated Logic: Regex-based Smart Extraction for OCR output.")
