import streamlit as st
import pdfplumber
import json

# পেজ সেটআপ
st.set_page_config(page_title="NID PDF to JSON Pro", layout="wide")

def clean_text(text):
    if text:
        # অপ্রয়োজনীয় স্পেস এবং ক্যারেক্টার ক্লিন করা
        text = text.replace('\n', ' ')
        return " ".join(text.split()).strip()
    return ""

def extract_nid_all_data(pdf_file):
    final_data = {}
    current_section = "" # অ্যাড্রেস সেকশন ট্র্যাকিং এর জন্য
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # টেবিল এক্সট্রাক্ট করা (আরও সেনসিটিভ সেটিংস দিয়ে)
            tables = page.extract_tables()
            
            for table in tables:
                for row in table:
                    # খালি রো বাদ দেওয়া
                    row = [clean_text(cell) for cell in row if cell is not None]
                    
                    if not row:
                        continue

                    # ১. যদি ২ কলামের রো হয় (Key: Value)
                    if len(row) == 2:
                        key, val = row[0], row[1]
                        if key and val:
                            # যদি কি (key) টা অ্যাড্রেস সেকশন হয়
                            if "Address" in key:
                                current_section = key
                            
                            # কি টা যদি অলরেডি থাকে, তবে ইউনিক করার জন্য সেকশন নাম যোগ করা
                            if key in final_data:
                                final_data[f"{current_section} {key}"] = val
                            else:
                                final_data[key] = val

                    # ২. যদি ৩ বা ৪ কলামের রো হয় (ঠিকানা বা এডুকেশন সেকশন)
                    elif len(row) >= 4:
                        # প্রথম জোড়া
                        k1, v1 = row[0], row[1]
                        # দ্বিতীয় জোড়া
                        k2, v2 = row[2], row[3]
                        
                        if k1 and v1:
                            final_data[f"{current_section} {k1}" if current_section else k1] = v1
                        if k2 and v2:
                            final_data[f"{current_section} {k2}" if current_section else k2] = v2
                            
    return final_data

# UI অংশ
st.title("📄 NID PDF Master Extractor")
st.write("এটি ১-৩ পেজের যেকোনো NID PDF থেকে সব ডাটা খুঁজে বের করবে।")

uploaded_file = st.file_uploader("আপনার PDF ফাইলটি আপলোড করুন", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('পুরো PDF স্ক্যান করা হচ্ছে...'):
            data = extract_nid_all_data(uploaded_file)
            
            if data:
                st.success(f"মোট {len(data)} টি ফিল্ড পাওয়া গেছে!")
                
                # JSON আউটপুট (বাংলা ফন্ট সাপোর্ট সহ)
                json_output = json.dumps(data, indent=4, ensure_ascii=False)
                
                tab1, tab2 = st.tabs(["📊 ডাটা ভিউ", "💻 JSON কোড"])
                
                with tab1:
                    # টেবিল আকারে সাজিয়ে দেখানো
                    st.table(data.items())
                
                with tab2:
                    st.code(json_output, language='json')
                    st.download_button(
                        label="Download JSON File",
                        data=json_output,
                        file_name="nid_extracted_data.json",
                        mime="application/json"
                    )
            else:
                st.error("দুঃখিত! PDF থেকে কোনো ডাটা পাওয়া যায়নি।")
                
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("নোট: বাংলা যুক্তবর্ণ '' আসার কারণ PDF এর নিজস্ব এনকোডিং। এটি ঠিক করতে হলে OCR (AI) ব্যবহার করতে হবে।")
