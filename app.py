import streamlit as st
import pdfplumber
import json
import re

st.set_page_config(page_title="NID Master Extractor", layout="wide")

def clean_val(text):
    if text:
        # অপ্রয়োজনীয় ক্যারেক্টার এবং নাল বাইট ক্লিন করা
        text = text.replace('\u0000', '').replace('\ufeff', '').replace('\n', ' ')
        # কিছু কমন এনকোডিং এরর ক্লিন করার চেষ্টা
        text = text.replace('', '') 
        return " ".join(text.split()).strip()
    return None

def extract_nid_structured(pdf_file):
    res = {
        "basic_info": {},
        "personal_info": {},
        "present_address": {},
        "permanent_address": {},
        "additional_info": {}
    }
    
    current_addr_section = None

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # টেবিল এক্সট্রাক্ট করা
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # সেলগুলো ক্লিন করা এবং খালি সেল বাদ দেওয়া
                    cells = [clean_val(c) for c in row if c is not None]
                    if not cells: continue
                    
                    row_text = " ".join([str(c) for c in cells])

                    # অ্যাড্রেস সেকশন ডিটেক্ট করা
                    if "Present Address" in row_text:
                        current_addr_section = "present_address"
                    elif "Permanent Address" in row_text:
                        current_addr_section = "permanent_address"

                    # কলাম অনুযায়ী ডাটা প্রসেস করা
                    # সাধারণত এনআইডি পিডিএফে [Key, Value, Key, Value] ফরম্যাট থাকে
                    i = 0
                    while i < len(cells):
                        key = cells[i]
                        if not key: 
                            i += 1
                            continue
                        
                        val = cells[i+1] if i+1 < len(cells) else None
                        key_lower = key.lower()

                        # ১. Basic Info Mapping
                        if any(x in key_lower for x in ["national id", "pin", "status", "afis status", "lock flag", "voter no", "form no", "sl no", "tag"]):
                            res["basic_info"][key_lower.replace(" ", "_")] = val
                        
                        # ২. Personal Info Mapping
                        elif any(x in key_lower for x in ["name", "date of birth", "birth place", "birth registration", "father name", "mother name", "spouse name", "gender", "marital", "occupation", "education", "religion"]):
                            res["personal_info"][key_lower.replace(" ", "_")] = val
                        
                        # ৩. Address Info (Present/Permanent)
                        elif any(x in key_lower for x in ["division", "district", "rmo", "upozila", "union/ward", "mouza", "moholla", "ward for", "village", "road", "holding", "post office", "postal code", "region"]):
                            if current_addr_section:
                                # মউজা/মহল্লা বা এই জাতীয় ফিল্ডগুলো ইউনিক করতে
                                cleaned_key = key_lower.replace("/", "_").replace(" ", "_")
                                res[current_addr_section][cleaned_key] = val
                        
                        # ৪. Additional Info Mapping
                        elif any(x in key_lower for x in ["blood group", "tin", "driving", "passport", "laptop id", "nid father", "nid mother", "nid spouse", "no finger", "voter area", "voter at"]):
                            res["additional_info"][key_lower.replace(" ", "_")] = val
                        
                        # ২ কলাম মুভ করা (Key এবং Value পার করে যাওয়া)
                        i += 2

    return res

st.title("📄 Professional NID Extractor (V2)")
st.write("এই ভার্সনটি 'checked' স্ট্যাটাসের পিডিএফ এবং মউজা/মহল্লা ডাটা নিখুঁতভাবে ধরার জন্য তৈরি।")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    with st.spinner('নিখুঁতভাবে স্ক্যান করা হচ্ছে...'):
        structured_data = extract_nid_structured(uploaded_file)
        
        # JSON আউটপুট
        final_json = json.dumps(structured_data, indent=2, ensure_ascii=False)
        
        st.success("এক্সট্রাকশন সম্পন্ন হয়েছে!")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Visual Data Tree")
            st.json(structured_data)
            
        with col2:
            st.subheader("Final JSON Response")
            st.code(final_json, language='json')
            st.download_button("Download JSON", final_json, file_name="nid_response.json")

st.divider()
st.info("নোট: কিছু পিডিএফ-এর ফন্ট এনকোডিং সমস্যার কারণে বাংলা যুক্তবর্ণ সঠিকভাবে নাও আসতে পারে।")
