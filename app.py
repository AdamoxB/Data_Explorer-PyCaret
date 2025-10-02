#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Explorer – PyCaret + ydata‑profiling

Features:
* Sidebar dataset selector or file uploader (CSV / Excel)
* Live data preview
* One‑click profiling report (HTML + PDF export)
"""

import os
import io
from typing import Optional

import streamlit as st
import pandas as pd
from pycaret.datasets import get_data
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
import pdfkit  # optional – will be used if available


# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #

def read_uploaded_file(file) -> pd.DataFrame:
    """Return a pandas DataFrame from an uploaded CSV / Excel file."""
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:  # .xlsx, .xls
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return pd.DataFrame()


def convert_html_to_pdf(html_str: str) -> Optional[bytes]:
    """Convert an HTML string to PDF bytes using wkhtmltopdf via pdfkit."""
    try:
        # temporary in‑memory buffer
        pdf_bytes = pdfkit.from_string(html_str, False)
        return pdf_bytes
    except Exception as e:
        st.warning(f"PDF conversion failed: {e}")
        return None


# --------------------------------------------------------------------------- #
# Streamlit UI – Sidebar
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="PyCaret Data Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a dark theme + nice spacing
CUSTOM_CSS = """
<style>
body {background: #111;}
.sidebar .sidebar-content {background: #222;}
.stButton>button, .stDownloadButton>button {
    background-color:#ff6f61; color:white;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("🔎 PyCaret Data Explorer")

# Sidebar widgets
with st.sidebar:
    st.header("📂 Select Dataset")
    # 1. Built‑in PyCaret datasets (you can add more if you like)
    builtin_ds = [
        "juice", "titanic", "diabetes", "winequality-red",
        "iris", "boston_housing", "adult"
    ]
    selected_builtin = st.selectbox("Choose a built‑in dataset", ["-- none --"] + builtin_ds)

    # 2. File uploader
    st.subheader("Upload your own data")
    uploaded_file = st.file_uploader(
        "CSV / Excel",
        type=["csv", "xlsx"],
        accept_multiple_files=False,
    )

# --------------------------------------------------------------------------- #
# Load Data – either from PyCaret or user upload
# --------------------------------------------------------------------------- #

df: pd.DataFrame | None = None

if selected_builtin != "-- none --":
    # load dataset from pycaret
    try:
        df = get_data(selected_builtin, profile=False)
        st.success(f"✅ Loaded **{selected_builtin}** dataset.")
    except Exception as e:
        st.error(f"Error loading built‑in dataset: {e}")

if uploaded_file is not None:
    # overwrite if user uploads a file
    df = read_uploaded_file(uploaded_file)
    if not df.empty:
        st.success("✅ Uploaded data loaded.")

# --------------------------------------------------------------------------- #
# Data preview
# --------------------------------------------------------------------------- #

if df is not None and not df.empty:
    st.subheader("📋 Data Preview")
    st.dataframe(df.head(10), use_container_width=True)

    # Button to generate profiling report
    if st.button("Generate Profiling Report"):
        with st.spinner("Creating the profile…"):
            try:
                profile = ProfileReport(
                    df,
                    title="Data Profiling",
                    explorative=True,
                    minimal=True,  # reduces size for quick rendering
                )
                st_profile_report(profile)  # renders inside Streamlit

                # HTML string for export
                html_str = profile.to_html()

                # ---- Export Buttons -------------------------------------------------
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download HTML",
                        data=html_str,
                        file_name=f"{selected_builtin or 'uploaded_data'}_profiling.html",
                        mime="text/html",
                    )
                with col2:
                    pdf_bytes = convert_html_to_pdf(html_str)
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{selected_builtin or 'uploaded_data'}_profiling.pdf",
                            mime="application/pdf",
                        )
            except Exception as e:
                st.error(f"Profiling failed: {e}")

else:
    st.info("Select a built‑in dataset or upload a CSV/Excel file to start.")
