import streamlit as st
import pdfplumber
import json

st.set_page_config(page_title="NID Master Extractor", layout="wide")

def clean_val(text):
    if text:
        # অপ্রয়োজনীয় ক্যারেক্টার এবং নাল বাইট ক্লিন করা
        text = text.replace('\u0000', '').replace('\ufeff', '').replace('\n', ' ')
        return " ".join(text.split()).strip()
    return None

def extract_nid_structured(pdf_file):
    # আপনার চাওয়া ফরম্যাট অনুযায়ী স্ট্রাকচার
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
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cells = [clean_val(c) for c in row if c is not None]
                    if not cells: continue
                    
                    row_text = " ".join([str(c) for c in cells])

                    # ঠিকানা সেকশন চিহ্নিত করা
                    if "Present Address" in row_text:
                        current_addr_section = "present_address"
                    elif "Permanent Address" in row_text:
                        current_addr_section = "permanent_address"

                    # ডেটা প্রসেসিং (Key-Value matching)
                    for i, cell in enumerate(cells):
                        if not cell: continue
                        
                        val = cells[i+1] if i+1 < len(cells) else None

                        # ১. Basic Info
                        if cell in ["National ID", "Pin", "Status", "Afis Status", "Lock Flag", "Voter No", "Form No", "Sl No", "Tag"]:
                            res["basic_info"][cell.lower().replace(" ", "_")] = val
                        
                        # ২. Personal Info
                        elif cell in ["Name(Bangla)", "Name(English)", "Date of Birth", "Birth Place", "Birth Registration No", "Father Name", "Mother Name", "Spouse Name", "Gender", "Marital", "Occupation", "Religion", "Education"]:
                            res["personal_info"][cell.lower().replace(" ", "_")] = val
                        
                        # ৩. Address Info (Present/Permanent)
                        elif cell in ["Division", "District", "RMO", "Upozila", "Union/Ward", "Mouza/Moholla", "Ward For Union Porishod", "Village/Road", "Home/Holding No", "Post Office", "Postal Code", "Region"]:
                            if current_addr_section:
                                res[current_addr_section][cell.lower().replace(" ", "_")] = val
                        
                        # ৪. Additional Info
                        elif cell in ["Blood Group", "TIN", "Driving", "Passport", "Laptop ID", "NID Father", "NID Mother", "Nid Spouse", "No Finger", "No Finger Print", "Voter Area", "Voter At"]:
                            res["additional_info"][cell.lower().replace(" ", "_")] = val

    return res

st.title("📄 Professional NID to JSON Extractor")
st.write("আপনার PDF ফাইলটি আপলোড করলে এটি অটোমেটিক ক্যাটাগরি অনুযায়ী সাজানো JSON দিবে।")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    with st.spinner('প্রসেসিং হচ্ছে...'):
        structured_data = extract_nid_structured(uploaded_file)
        
        # JSON আউটপুট
        final_json = json.dumps(structured_data, indent=2, ensure_ascii=False)
        
        st.success("সফলভাবে ক্যাটাগরি অনুযায়ী সাজানো হয়েছে!")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Tree View")
            st.json(structured_data)
            
        with col2:
            st.subheader("Raw JSON Response")
            st.code(final_json, language='json')
            st.download_button("Download JSON", final_json, file_name="nid_response.json")

st.divider()
st.caption("Auto-delete: ব্রাউজার বন্ধ করলে কোনো ডেটা সেভ থাকবে না।")
