import streamlit as st
import pdfplumber
import json

# পেজ সেটআপ
st.set_page_config(page_title="NID PDF to JSON Pro", layout="wide")

def clean_text(text):
    if text:
        # বাংলা লেখার মাঝখানের অতিরিক্ত স্পেস কমানোর চেষ্টা
        return " ".join(text.split()).strip()
    return ""

def extract_nid_data(pdf_file):
    extracted_dict = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # টেবিল এক্সট্রাক্ট করার সময় সেটিংস আরও নিখুঁত করা হয়েছে
            tables = page.extract_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
            })
            
            for table in tables:
                for row in table:
                    # ১. যদি রো-তে ২টা কলাম থাকে (সাধারণ ফিল্ড)
                    if len(row) == 2:
                        key = clean_text(row[0])
                        val = clean_text(row[1])
                        if key and val:
                            extracted_dict[key] = val
                            
                    # ২. যদি রো-তে ৪টা কলাম থাকে (ঠিকানা বা এডুকেশন সেকশন)
                    elif len(row) == 4:
                        # প্রথম জোড়া (Division: Khulna)
                        key1 = clean_text(row[0])
                        val1 = clean_text(row[1])
                        if key1 and val1:
                            extracted_dict[key1] = val1
                            
                        # দ্বিতীয় জোড়া (District: Satkhira)
                        key2 = clean_text(row[2])
                        val2 = clean_text(row[3])
                        if key2 and val2:
                            extracted_dict[key2] = val2
                            
    return extracted_dict

st.title("📄 Advanced NID PDF Extractor")
st.write("এই টুলটি বিশেষভাবে NID সার্ভার কপির অ্যাড্রেস এবং বাংলা ফন্ট ঠিকভাবে রিড করার জন্য তৈরি।")

uploaded_file = st.file_uploader("আপনার PDF ফাইলটি এখানে আপলোড করুন", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('নিখুঁতভাবে ডাটা এক্সট্রাক্ট করা হচ্ছে...'):
            data = extract_nid_data(uploaded_file)
            
            if data:
                st.success("এক্সট্রাকশন সম্পন্ন হয়েছে!")
                
                # JSON ফরম্যাট (ensure_ascii=False দিলে বাংলা ঠিক থাকবে)
                json_output = json.dumps(data, indent=4, ensure_ascii=False)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📋 Extracted Data")
                    # ডাটা সুন্দরভাবে সাজিয়ে দেখানো
                    for k, v in data.items():
                        st.markdown(f"**{k}:** {v}")
                
                with col2:
                    st.subheader("💻 JSON Output")
                    st.code(json_output, language='json')
                    
                    st.download_button(
                        label="Download JSON File",
                        data=json_output,
                        file_name=f"nid_data_{data.get('National ID', 'file')}.json",
                        mime="application/json"
                    )
            else:
                st.warning("কোনো টেবিল ডাটা খুঁজে পাওয়া যায়নি।")
                
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("দ্রষ্টব্য: PDF-এর ফন্ট এনকোডিং জটিল হলে কিছু বাংলা যুক্তবর্ণ ভেঙে যেতে পারে। এটি সরাসরি PDF লাইব্রেরির সীমাবদ্ধতা।")
