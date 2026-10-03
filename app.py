import os
import streamlit as st
from config import OPENROUTER_API_KEY, FREE_MODELS
from ingest_code import LargeCodebaseIngestor
from agents import LegacyLensMultiAgentPipeline

st.set_page_config(page_title="LegacyLens AI - OpenRouter Multi-Agent", layout="wide")

st.title("🕵️ LegacyLens AI: Autonomous Code Archeologist")
st.subheader("Reverse-engineer 5-6 GB Java Codebases into IEEE FRS & SRS Documents")

# Sidebar Configuration
st.sidebar.header("🔑 API & Model Configuration")
api_key = st.sidebar.text_input("OpenRouter API Key", value=OPENROUTER_API_KEY, type="password")
selected_model = st.sidebar.selectbox("Select OpenRouter Free Model", FREE_MODELS)

st.sidebar.markdown("---")
st.sidebar.info("Supports recursive decompression of `.rar` and `.zip` source files containing JSP, Servlets, JavaBeans, and XML configs.")

# File Upload Section
uploaded_files = st.file_uploader(
    "Upload Source Archives (.rar, .zip)", 
    type=["rar", "zip"], 
    accept_multiple_files=True
)

if st.button("🚀 Start Autonomous Analysis & Generation") and uploaded_files:
    if not api_key:
        st.error("Please provide a valid OpenRouter API Key in the sidebar.")
    else:
        # Step 1: Save & Extract Archives
        st.info("Step 1/4: Decompressing and cataloging code archives...")
        ingestor = LargeCodebaseIngestor()
        saved_paths = []
        
        for file in uploaded_files:
            temp_path = os.path.join("./temp_uploads", file.name)
            os.makedirs("./temp_uploads", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            saved_paths.append(temp_path)

        ingestor.extract_archives(saved_paths)
        catalog = ingestor.scan_and_catalog()
        
        st.success(f"Extracted & Cataloged {catalog['stats']['total_files']} source files ({catalog['stats']['total_size_mb']} MB).")

        # Step 2: Batch Analysis (Map Phase)
        st.info("Step 2/4: Running Code Analyst Agents across code batches...")
        pipeline = LegacyLensMultiAgentPipeline(api_key=api_key)
        
        all_files = catalog["presentation_layer"] + catalog["business_layer"] + catalog["config_layer"]
        batches = ingestor.create_batches(all_files, batch_size=15)
        
        progress_bar = st.progress(0)
        module_analyses = []
        
        for idx, batch in enumerate(batches):
            analysis = pipeline.agent_code_analyst(batch)
            module_analyses.append(analysis)
            progress_bar.progress((idx + 1) / len(batches))
            
        st.success("Batch analysis complete.")

        # Step 3: Synthesize IEEE FRS
        st.info("Step 3/4: Synthesizing IEEE 830 / ISO 29148 Compliant FRS Document...")
        frs_doc = pipeline.agent_frs_synthesizer(module_analyses)

        # Step 4: Synthesize IEEE SRS
        st.info("Step 4/4: Synthesizing IEEE 830 Compliant SRS Document...")
        srs_doc = pipeline.agent_srs_synthesizer(module_analyses, catalog["stats"])

        # Display Outputs & Downloads
        st.markdown("---")
        st.header("📄 Generated IEEE Documentation")
        
        tab1, tab2 = st.tabs(["Functional Requirements Specification (FRS)", "Software Requirements Specification (SRS)"])
        
        with tab1:
            st.markdown(frs_doc)
            st.download_button(
                label="Download FRS (.md)",
                data=frs_doc,
                file_name="IEEE_Functional_Requirements_Specification.md",
                mime="text/markdown"
            )
            
        with tab2:
            st.markdown(srs_doc)
            st.download_button(
                label="Download SRS (.md)",
                data=srs_doc,
                file_name="IEEE_Software_Requirements_Specification.md",
                mime="text/markdown"
            )
