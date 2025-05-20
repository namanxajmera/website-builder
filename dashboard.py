import streamlit as st
import subprocess
import os
import sys
from pathlib import Path

# --- UI ---
st.set_page_config(page_title="Website Modernizer & AI Rebuilder", layout="wide")
st.title("Website Modernizer & AI Rebuilder")
st.markdown("Enter a website URL to crawl and modernize with Google Gemini AI.")

url = st.text_input("Website URL", "https://")
run_btn = st.button("Crawl & Modernize Site")

output_area = st.empty()

# --- Main logic ---
def run_crawl_and_remake(url):
    domain = url.split("//")[-1].split("/")[0]
    # 1. Run crawl_site.py
    crawl_cmd = [sys.executable, "crawl_site.py", url]
    st.info(f"Crawling {url} ...")
    crawl_proc = subprocess.run(crawl_cmd, capture_output=True, text=True)
    if crawl_proc.returncode != 0:
        st.error(f"Crawl failed: {crawl_proc.stderr}")
        return
    # Find the output folder (domain or domain_N)
    candidates = sorted([f for f in os.listdir(".") if f.startswith(domain) and os.path.isdir(f) and not f.endswith("_ai")], key=os.path.getmtime, reverse=True)
    if not candidates:
        st.error("No crawl output folder found.")
        return
    site_folder = candidates[0]
    # 2. Run remake_site_with_ai.py with streaming
    remake_cmd = [sys.executable, "remake_site_with_ai.py", site_folder, "--stream"]
    st.info(f"Remaking site with Gemini AI ...")
    with st.status("AI is rebuilding the site... (streaming)", expanded=True) as status:
        html_chunks = []
        with subprocess.Popen(remake_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
            for line in proc.stdout:
                # Stream only the AI-generated HTML (not logs)
                if line.startswith("[INFO]") or line.startswith("[SUCCESS]") or line.startswith("[WARN]") or line.startswith("[ERROR]") or line.startswith("[DONE]"):
                    status.write(line.rstrip())
                else:
                    html_chunks.append(line)
                    output_area.markdown("".join(html_chunks), unsafe_allow_html=True)
        if proc.wait() == 0:
            status.update(label="AI site remake complete!", state="complete")
        else:
            status.update(label="AI site remake failed.", state="error")
    st.success(f"Done! Modernized site output in: {site_folder}_ai/")

if run_btn and url and url.startswith("http"):
    run_crawl_and_remake(url) 