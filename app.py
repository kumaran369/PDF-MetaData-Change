import streamlit as st
import pikepdf
import tempfile
import zipfile
import os
from PyPDF2 import PdfReader
from io import BytesIO

# Inject CSS for styling and mobile responsiveness
st.markdown(
    """
    <style>
    /* Container max width */
    .main > div.block-container {
        max-width: 600px;
        margin: auto;
        padding: 1rem;
    }

    /* Header styling */
    h1 {
        color: #0a58ca;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    /* Buttons styling */
    div.stButton > button {
        background-color: #0a58ca;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
        margin-bottom: 1rem;
        transition: background-color 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #084298;
        cursor: pointer;
    }

    /* Text input styling */
    .stTextInput>div>div>input {
        width: 100%;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #0a58ca;
        font-size: 1rem;
    }

    /* Preview box styling */
    .preview-box {
        background-color: #f0f8ff;
        border: 1px solid #0a58ca;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Mobile responsive */
    @media (max-width: 480px) {
        .main > div.block-container {
            padding: 0.5rem;
            max-width: 100%;
        }
        div.stButton > button {
            font-size: 1rem;
            padding: 0.75rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

def read_metadata(file):
    try:
        reader = PdfReader(file)
        info = reader.metadata
        def clean_key(k):
            return k[1:] if k.startswith("/") else k
        meta = {"Author": "", "Title": "", "Subject": "", "Keywords": ""}
        if info:
            for k, v in info.items():
                ck = clean_key(k)
                if ck in meta and v is not None:
                    meta[ck] = str(v)
        return meta
    except Exception:
        return {"Author": "", "Title": "", "Subject": "", "Keywords": ""}

st.title("📄 PDF Metadata Bulk Editor — Edit Author Only")

# Initialize session state variables
if "author_input" not in st.session_state:
    st.session_state.author_input = "Citigroup"
if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False

def clear_all():
    st.session_state.author_input = "Citigroup"
    st.session_state.clear_uploader = not st.session_state.clear_uploader

if st.button("🧹 Clear Form"):
    clear_all()

uploader_key = "file_uploader_" + str(st.session_state.clear_uploader)

uploaded_files = st.file_uploader(
    "Upload PDF files (multiple allowed)",
    type="pdf",
    accept_multiple_files=True,
    key=uploader_key
)

author = st.text_input(
    "Author",
    key="author_input"
)

if uploaded_files:
    st.markdown("### 🔍 Preview Uploaded PDFs Metadata")
    for file in uploaded_files:
        file_bytes = file.read()
        meta = read_metadata(BytesIO(file_bytes))
        st.markdown(
            f'<div class="preview-box"><strong>{file.name}</strong><br>'
            f'Author: {meta["Author"]} <br>'
            f'Title: {meta["Title"]} <br>'
            f'Subject: {meta["Subject"]} <br>'
            f'Keywords: {meta["Keywords"]}</div>',
            unsafe_allow_html=True
        )
        file.seek(0)

st.markdown("---")

if st.button("✅ Apply Author Metadata & Download"):
    if not uploaded_files:
        st.error("Please upload at least one PDF file.")
    else:
        if len(uploaded_files) == 1:
            uploaded_file = uploaded_files[0]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file.flush()
                temp_path = tmp_file.name
            try:
                with pikepdf.Pdf.open(temp_path) as pdf:
                    if author.strip():
                        pdf.docinfo["/Author"] = author
                    new_name = os.path.splitext(uploaded_file.name)[0] + "-CG.pdf"
                    output_stream = BytesIO()
                    pdf.save(output_stream)
                    output_stream.seek(0)
                    st.success("🎉 File processed and ready for download!")
                    st.download_button(
                        "📥 Download Edited PDF",
                        data=output_stream,
                        file_name=new_name,
                        mime="application/pdf"
                    )
            except pikepdf.PdfError as e:
                st.error(f"Error processing PDF: {e}")
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        else:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file.flush()
                        temp_path = tmp_file.name
                    try:
                        with pikepdf.Pdf.open(temp_path) as pdf:
                            if author.strip():
                                pdf.docinfo["/Author"] = author
                            new_name = os.path.splitext(uploaded_file.name)[0] + "-CG.pdf"
                            fd, temp_out_path = tempfile.mkstemp(suffix=".pdf")
                            os.close(fd)
                            pdf.save(temp_out_path)
                            zipf.write(temp_out_path, arcname=new_name)
                            os.remove(temp_out_path)
                    except pikepdf.PdfError as e:
                        st.warning(f"Skipping {uploaded_file.name}: {e}")
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
            zip_buffer.seek(0)
            st.success("🎉 Files processed and ready for download!")
            st.download_button(
                "📦 Download All Modified PDFs (ZIP)",
                data=zip_buffer,
                file_name="modified_pdfs.zip",
                mime="application/zip"
            )
