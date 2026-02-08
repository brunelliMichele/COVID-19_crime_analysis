import subprocess
import sys
import time
import re
import streamlit as st
from pathlib import Path

# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false

# ---------- App configuration ----------
st.set_page_config(
    page_title="COVID-19 and criminality in Italy",
    layout="wide"
)


# ---------- Data check at startup ----------
DATA_PATH = Path(__file__).parent.parent / "data"

def check_and_setup_data():
    """Check if data exists, if not run setup."""
    required_files = [
        DATA_PATH / "processed/criminality_clean.parquet",
        DATA_PATH / "shapes/nuts1_it.geoparquet",
        DATA_PATH / "shapes/nuts2_it.geoparquet",
        DATA_PATH / "shapes/nuts3_it.geoparquet",
        DATA_PATH / "raw/delittips_9_2014.csv",
        DATA_PATH / "raw/delittips_9_2015.csv",
        DATA_PATH / "raw/delittips_9_2016.csv",
        DATA_PATH / "raw/delittips_9_2017.csv",
        DATA_PATH / "raw/delittips_9_2018.csv",
        DATA_PATH / "raw/delittips_9_2019.csv",
        DATA_PATH / "raw/delittips_9_2020.csv",
        DATA_PATH / "raw/delittips_9_2021.csv",
        DATA_PATH / "raw/delittips_9_2022.csv",
        DATA_PATH / "raw/delittips_9_2023.csv"
    ]

    missing = [f for f in required_files if not f.exists()]

    if not missing:
        return
    

    # hide sidebar during setup
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.title("Initial Setup")
    st.warning("Data not found. Running initial setup...")

    st.info("""
    **What's happening:**
    - Downloading 10 years of crime data from ISTAT API (2014-2023)
    - Each year require separate API call
    - Total: ~10 files to download
    
    **Estimated time:** 2-3 minutes (depending on connection speed)
    """)

    scripts_dir = Path(__file__).parent.parent / "scripts"

    # Step 1: Fetch data
    st.markdown("### Step 1/3: Fetching data from ISTAT")
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    pat = re.compile(r"\[(\d+)\s*/\s*(\d+)\]")

    # run fetch script and capture output
    process = subprocess.Popen(
        [sys.executable, "-u", scripts_dir / "fetch_data_istat.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    if process.stdout:
        for line in process.stdout:
            status_text.text(line.strip())

            m = pat.search(line)
            if m:
                cur = int(m.group(1))
                tot = int(m.group(2))
                progress_bar.progress(min(cur / tot, 1.0))

    process.wait()
    if process.returncode != 0:
        progress_bar.progress(0.0)
        status_text.text("Data fetch failed")
        st.error(f"fetch_data_istat.py exited with code {process.returncode}")
        st.stop()


    progress_bar.progress(1.0)
    status_text.text("Data fetched succesfully!")

    # Step 2: Clean data
    st.markdown("### Step 2/3: Cleaning data")
    with st.spinner("Processing and cleaning datasets..."):
        subprocess.run([sys.executable, scripts_dir / "clean_data.py"], check=True)
    st.text("Data cleaned succesfully!")

    # Step 3: Build shapes
    st.markdown("### Step 3/3: Building shapefiles")
    with st.spinner("Preparing geographic boundaries..."):
        subprocess.run([sys.executable, scripts_dir / "build_shapes.py"], check=True)
    st.text("Shapefiles ready!")

    st.success("Setup complete! The app will now reload.")
    st.balloons()

    time.sleep(2)
    st.rerun()

check_and_setup_data()

# ---------- Navigation ----------
pages = {
    "Home": [
        st.Page("pages/home.py", title="Home"),
    ],
    "Analysis": [
        st.Page("pages/01_variation_maps.py", title="Spatial Distribution of Crime Changes"),
        st.Page("pages/02_moran.py", title="Spatial Autocorrelation Analysis"),
        st.Page("pages/03_lisa_transitions.py", title="LISA Cluster Transitions"),
    ]
}

pg = st.navigation(pages)
pg.run()