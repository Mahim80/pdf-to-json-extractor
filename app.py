import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import json
import re

# পেজ সেটআপ
st.set_page_config(page_title="AI NID Extractor Pro", layout="wide")

st.title("📄 Professional AI NID Extractor")
st.write("এটি OCR এর মাধ্যমে পাওয়া অগোছালো টেক্সট থেকে বুদ্ধিমান উপায়ে ডাটা খুঁজে বের করে।")

def advanced_parse(text_list):
    # সব টেক্সটকে একটি বড় স্ট্রিং এ রূপান্তর
    content = " ".join(text_list).replace("\n", " ")
    
    res = {
        "basic_info": {},
        "personal_info": {},
        "present_address": {},
        "permanent_address": {},
        "additional_info": {}
    }

    # ডাটা খোঁজার স্মার্ট লজিক ফাংশন
    def find_data(keywords, length=20, is_digit=False):
        for word in keywords:
            if word in content:
                # কি-ওয়ার্ড এর পরের অংশটুকু কেটে নেওয়া
                start_idx = content.find(word) + len(word)
                extracted = content[start_idx : start_idx + 60].strip()
                
                if is_digit:
                    digits = re.findall(r'\d+', extracted)
                    return digits[0] if digits else ""
                
                # প্রথম শব্দ বা দুই শব্দ নেওয়া
                parts = extracted.split()
                return " ".join(parts[:3]) if parts else ""
        return ""

    # ১. Basic Info
    res["basic_info"]["national_id"] = find_data(["National ID", "ID No"], is_digit=True)
    res["basic_info"]["pin"] = find_data(["Pin"], is_digit=True)
    res["basic_info"]["voter_no"] = find_data(["Voter No"], is_digit=True)
    
    # ২. Personal Info
    res["personal_info"]["name_bangla"] = find_data(["Name(Bangla)", "নাম (বাংলা)"])
    res["personal_info"]["name_english"] = find_data(["Name(English)", "নাম (ইংরেজি)"])
    res["personal_info"]["father_name"] = find_data(["Father Name", "পিতা"])
    res["personal_info"]["mother_name"] = find_data(["Mother Name", "মাতা"])
    res["personal_info"]["date_of_birth"] = find_data(["Date of Birth", "জন্ম তারিখ"])

    # ৩. Address (Present)
    # অ্যাড্রেস খুঁজে বের করার জন্য 'Present Address' এর পরের অংশ স্ক্যান করা
    if "Present Address" in content:
        addr_part = content[content.find("Present Address") : content.find("Permanent Address")]
        res["present_address"]["division"] = re.search(r"Division\s*(\S+)", addr_part).group(1) if re.search(r"Division\s*(\S+)", addr_part) else ""
        res["present_address"]["district"] = re.search(r"District\s*(\S+)", addr_part).group(1) if re.search(r"District\s*(\S+)", addr_part) else ""
        res["present_address"]["upozila"] = re.search(r"Upozila\s*(\S+)", addr_part).group(1) if re.search(r"Upozila\s*(\S+)", addr_part) else ""
        res["present_address"]["postal_code"] = re.search(r"Postal Code\s*(\d+)", addr_part).group(1) if re.search(r"Postal Code\s*(\d+)", addr_part) else ""

    # ৪. Additional Info
    res["additional_info"]["laptop_id"] = find_data(["Laptop ID"])
    res["additional_info"]["nid_father"] = find_data(["NID Father"], is_digit=True)
    res["additional_info"]["nid_mother"] = find_data(["NID Mother"], is_digit=True)

    return res

uploaded_file = st.file_uploader("Upload NID PDF", type=['pdf'])

if uploaded_file is not None:
    try:
        with st.spinner('AI OCR ডাটা প্রসেস করছে... (DPI ইমপ্রুভ করা হচ্ছে)'):
            # ১. PDF থেকে হাই-কোয়ালিটি ইমেজ (DPI 400)
            images = convert_from_bytes(uploaded_file.read(), dpi=400)
            
            all_text_lines = []
            for img in images:
                # ২. OCR (বাংলা ও ইংরেজি)
                text = pytesseract.image_to_string(img, lang='ben+eng')
                all_text_lines.append(text)
            
            # ৩. স্মার্ট পার্সিং
            final_data = advanced_parse(all_text_lines)
            
            st.success("এক্সট্রাকশন সম্পন্ন!")
            
            final_json = json.dumps(final_data, indent=4, ensure_ascii=False)
            
            tab1, tab2, tab3 = st.tabs(["📊 ফলাফল", "💻 JSON কোড", "📝 Raw OCR Text"])
            
            with tab1:
                st.json(final_data)
            with tab2:
                st.code(final_json, language='json')
                st.download_button("Download JSON", final_json, file_name="nid_result.json")
            with tab3:
                st.text_area("OCR এর মাধ্যমে পাওয়া কাঁচা লেখা (Debug):", "\n".join(all_text_lines), height=400)

    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("Developed with Python Tesseract Engine")
