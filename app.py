import streamlit as st
import pdfplumber
import json

# Page config
st.set_page_config(page_title="NID PDF to JSON", layout="wide")

def clean_text(text):
    if text:
        return " ".join(text.split())
    return ""

def extract_nid_data(pdf_file):
    all_data = {}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if len(row) >= 2:
                        key = clean_text(row[0])
                        val = clean_text(row[1])
                        if key and val:
                            all_data[key] = val
                    
                    # For address sections with 4 columns
                    if len(row) == 4:
                        key2 = clean_text(row[2])
                        val2 = clean_text(row[3])
                        if key2 and val2:
                            all_data[key2] = val2
    return all_data

st.title("📄 NID PDF to JSON Extractor")
st.write("আপনার PDF ফাইলটি আপলোড করুন। উইন্ডো বন্ধ করলে ডাটা অটো মুছে যাবে।")

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('প্রসেস হচ্ছে...'):
            data = extract_nid_data(uploaded_file)
            
            if data:
                st.success("এক্সট্রাকশন সফল হয়েছে!")
                
                # Convert to JSON string
                json_output = json.dumps(data, indent=4, ensure_all_chars=False)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Field Data")
                    st.json(data)
                
                with col2:
                    st.subheader("JSON Code")
                    st.code(json_output, language='json')
                    
                    st.download_button(
                        label="Download JSON File",
                        data=json_output,
                        file_name="extracted_nid.json",
                        mime="application/json"
                    )
            else:
                st.error("কোনো ডাটা পাওয়া যায়নি।")
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("Privacy Note: আপনার ফাইল হার্ডডিস্কে সেভ হয় না, শুধু র‍্যাম-এ প্রসেস হয়।")
