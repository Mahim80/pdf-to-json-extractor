import streamlit as st
import pdfplumber
import json

st.set_page_config(page_title="NID Master Extractor", layout="wide")

def clean_val(text):
    if text:
        # \u0000 এবং অপ্রয়োজনীয় ক্যারেক্টার রিমুভ করা
        text = text.replace('\u0000', '').replace('\n', ' ')
        return " ".join(text.split()).strip()
    return ""

def process_nid_pdf(pdf_file):
    data = {}
    current_section = ""

    # আমরা জানি এই ফিল্ডগুলো পিডিএফে আছে
    target_keys = [
        "National ID", "Pin", "Status", "Afis Status", "Lock Flag", "Voter No", 
        "Form No", "Sl No", "Tag", "Name(Bangla)", "Name(English)", 
        "Date of Birth", "Birth Place", "Birth Registration No", "Father Name", 
        "Mother Name", "Spouse Name", "Gender", "Marital", "Occupation", 
        "Education", "Blood Group", "Religion", "Laptop ID", "NID Father", 
        "NID Mother", "Nid Spouse", "Voter Area", "Voter At"
    ]
    
    address_fields = ["Division", "District", "RMO", "Upozila", "Union/Ward", "Mouza/Moholla", "Ward For Union Porishod", "Village/Road", "Home/Holding No", "Post Office", "Postal Code", "Region"]

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # রো ক্লিন করা
                    cells = [clean_val(c) for c in row if c is not None]
                    if not cells: continue

                    # সেকশন চেক (Present/Permanent Address)
                    row_str = " ".join(cells)
                    if "Present Address" in row_str:
                        current_section = "Present"
                    elif "Permanent Address" in row_str:
                        current_section = "Permanent"

                    # ডাটা এক্সট্রাক্ট করা
                    for i in range(len(cells)):
                        cell = cells[i]
                        
                        # ১. সাধারণ ফিল্ড চেক
                        if cell in target_keys:
                            if i + 1 < len(cells) and cells[i+1] not in target_keys:
                                data[cell] = cells[i+1]
                        
                        # ২. অ্যাড্রেস ফিল্ড চেক
                        if cell in address_fields and current_section:
                            key_name = f"{current_section}_{cell}"
                            if i + 1 < len(cells):
                                # কিছু ক্ষেত্রে ভ্যালু আগে বা পরে থাকতে পারে, তাই চেক করা
                                val = cells[i+1]
                                if val not in address_fields and val not in target_keys:
                                    data[key_name] = val

    return data

st.title("📄 NID PDF to JSON master Extractor")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    extracted_data = process_nid_pdf(uploaded_file)
    
    if extracted_data:
        st.success("Data Extracted Successfully!")
        
        # JSON আউটপুট
        final_json = json.dumps(extracted_data, indent=4, ensure_ascii=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Field View")
            st.write(extracted_data)
            
        with col2:
            st.subheader("JSON Output")
            st.code(final_json, language='json')
            st.download_button("Download JSON", final_json, file_name="nid_data.json")
    else:
        st.error("No data found in PDF.")

st.divider()
st.caption("Note: This version uses a Smart Key-Value matching logic for NID formats.")
