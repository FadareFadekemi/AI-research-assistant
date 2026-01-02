import streamlit as st
import requests
import os

# --- CONFIGURATION ---
API_URL = "https://aira-3eyc.onrender.com/research/run"
DOWNLOAD_URL = "https://aira-3eyc.onrender.com/download"

st.set_page_config(
    page_title="AIRA | Advanced Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DEEP ACADEMIC THEME (LEGIBILITY FIXES) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0F172A; }}
    .stApp, .stMarkdown, p, li, span, label {{ color: #F8FAFC !important; }}

    /* Sidebar and Toggle Button */
    section[data-testid="stSidebar"] {{ background-color: #1E293B !important; border-right: 1px solid #334155 !important; }}
    button[aria-label="Expand sidebar"], button[aria-label="Collapse sidebar"] {{
        background-color: #60A5FA !important; color: #0F172A !important;
    }}

    /* Chat Messages */
    [data-testid="stChatMessage"] {{ background-color: #1E293B !important; border: 1px solid #334155 !important; border-radius: 15px; margin-bottom: 10px; }}
    
    /* File Uploader */
    [data-testid="stFileUploader"] section {{ background-color: #0F172A !important; border: 2px dashed #60A5FA !important; }}
    
    /* Download Buttons */
    .stDownloadButton button {{
        background-color: #60A5FA !important; color: #0F172A !important;
        font-weight: bold; width: 100%; border-radius: 8px;
    }}

    /* Context Menu / Three Dots Fix */
    div[data-baseweb="popover"], div[data-baseweb="menu"] {{ background-color: #1E293B !important; color: #F8FAFC !important; }}
    </style>
""", unsafe_allow_html=True)

# --- CACHING UTILITY ---
@st.cache_data(show_spinner=False)
def get_file_content(url):
    """Downloads file once and stores it in cache to prevent repeated backend hits."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
    except Exception:
        return None
    return None

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: CONTROLS & UPLOAD ---
with st.sidebar:
    st.title("🔬 AIRA Workspace")
    st.info("Upload your dataset below to begin statistical analysis.")
    
    dataset = st.file_uploader("Select Research Data (CSV/XLSX)", type=["csv", "xlsx"])
    
    if dataset:
        st.success(f"✅ Loaded: {dataset.name}")
    
    st.markdown("---")
    if st.button("🗑️ Clear Research Session", use_container_width=True):
        st.session_state.messages = []
        st.cache_data.clear()  # Clear cache when session is cleared
        st.rerun()

# --- HEADER ---
st.title("🧠 AIRA")
st.caption("Integrated AI Research Assistant | Literature • Analysis • Narrative Discussion")

# --- UTILITY: RENDERER FOR VISUALS & FILES ---
def render_research_outputs(visuals, exports, msg_idx):
    """Displays images and download buttons using cached data and unique keys."""
    if visuals:
        st.markdown("### 📊 Statistical Visualizations")
        cols = st.columns(min(len(visuals), 2))
        for idx, (name, path) in enumerate(visuals.items()):
            with cols[idx % 2]:
                image_url = f"{DOWNLOAD_URL}/{path}"
                img_content = get_file_content(image_url)
                if img_content:
                    st.image(img_content, caption=name, use_container_width=True)

    if exports:
        st.markdown("### 📁 Downloadable Research Assets")
        exp_cols = st.columns(len(exports))
        for idx, (key, path) in enumerate(exports.items()):
            if not path: continue
            
            final_path = path[0] if isinstance(path, list) else path
            file_name = os.path.basename(final_path)
            file_url = f"{DOWNLOAD_URL}/{final_path}"
            
            with exp_cols[idx]:
                # Use cached content for the download button
                file_bytes = get_file_content(file_url)
                if file_bytes:
                    st.download_button(
                        label=f"💾 Download {key.upper()}",
                        data=file_bytes,
                        file_name=file_name,
                        # Unique key using message index and file name hash to prevent duplicates
                        key=f"btn_{msg_idx}_{idx}_{hash(final_path)}"
                    )
                else:
                    st.error("Failed to load asset.")

# --- MAIN CHAT INTERFACE ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg.get("content", ""))
        render_research_outputs(msg.get("visuals"), msg.get("exports"), i)

# --- INPUT AREA ---
if user_prompt := st.chat_input("How can I help with your research today?"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.spinner("🔍 AIRA is thinking, analyzing, and writing..."):
        try:
            files = {"dataset": dataset} if dataset else None
            data = {"message": user_prompt}
            
            response = requests.post(API_URL, data=data, files=files)
            
            if response.status_code == 200:
                res_data = response.json()
                
                content = res_data.get("content", "Analysis complete.")
                visuals = res_data.get("visuals", {})
                exports = res_data.get("exports", {})

                with st.chat_message("assistant"):
                    st.markdown(content)
                    render_research_outputs(visuals, exports, len(st.session_state.messages))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": content,
                    "visuals": visuals,
                    "exports": exports
                })
            else:
                st.error(f"⚠️ Backend Error: {response.text}")
        
        except Exception as e:
            st.error(f"❌ Connection Failed: {str(e)}")

st.markdown("---")
st.caption("Powered by AIRA Pipeline v2.0 | Optimized for High-Contrast Academic Environments")