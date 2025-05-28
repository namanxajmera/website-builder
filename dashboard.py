import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup # Added for parsing HTML
from urllib.parse import urlparse, urljoin # Added for link processing
import time
import threading

# --- Initialize session state ---
if 'current_preview_page_id' not in st.session_state:
    st.session_state.current_preview_page_id = None
if 'ai_output_folder' not in st.session_state:
    st.session_state.ai_output_folder = None
if 'log_text' not in st.session_state:
    st.session_state.log_text = "" # For Streamlit UI display
if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'current_step' not in st.session_state: # For UI step indicators
    st.session_state.current_step = ""
if 'step_status' not in st.session_state: # For UI step indicators
    st.session_state.step_status = {}

# --- UI ---
st.set_page_config(page_title="Website Modernizer & AI Rebuilder", layout="wide")
st.title("🤖 Website Modernizer & AI Rebuilder")
st.markdown("Enter a website URL to crawl and modernize with Google Gemini AI.")

url_input = st.text_input("Website URL", "https://example.com", key="url_input_key")

# --- Enhanced Logging for Streamlit UI ---
def append_log_to_ui(raw_message_from_subprocess):
    """Appends raw subprocess message to Streamlit UI log"""
    st.session_state.log_text += raw_message_from_subprocess # Newline handled by subprocess

def clear_ui_logs():
    """Clear logs in UI and internal state"""
    st.session_state.log_text = ""
    st.session_state.step_status = {}
    st.session_state.current_step = ""

def update_step_status(step_key, status, step_name_for_ui=""):
    """Update the status of a processing step for UI display"""
    st.session_state.step_status[step_key] = status
    if status == "running" and step_name_for_ui:
        st.session_state.current_step = step_name_for_ui
    elif status != "running" and st.session_state.current_step == step_name_for_ui : # Clear if this step completed/errored
        st.session_state.current_step = ""

# --- Core Logic (HTML Preview, etc.) ---
def modify_html_for_preview(html_content, current_page_id, ai_output_folder_path):
    soup = BeautifulSoup(html_content, "html.parser")
    global_css_path = Path(ai_output_folder_path) / "global_styles.css"
    if global_css_path.exists():
        with open(global_css_path, "r", encoding="utf-8") as f_css:
            css_content = f_css.read()
        for link_tag in soup.find_all('link', rel='stylesheet'):
            if 'global_styles.css' in link_tag.get('href', ''):
                link_tag.decompose()
        style_tag = soup.new_tag('style')
        style_tag.string = css_content
        if soup.head: soup.head.append(style_tag)
        else: soup.insert(0, style_tag)

    available_page_ids = [
        d.name for d in Path(ai_output_folder_path).iterdir() 
        if d.is_dir() and (d / "index.html").exists()
    ]
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        parsed_href = urlparse(href)
        if parsed_href.scheme or parsed_href.netloc:
            a_tag['target'] = '_blank'
            continue
        target_page_id = None
        match = re.match(r"^(?:\.\./)?([^/]+)(?:/index\.html|/)?$", href)
        if match:
            potential_id = match.group(1)
            if potential_id in available_page_ids:
                target_page_id = potential_id
        if target_page_id:
            a_tag['href'] = f"/?preview_page={target_page_id}"
            a_tag['target'] = '_self'
    return str(soup)

def display_preview(page_id_to_display, ai_folder_path_str):
    ai_folder_path = Path(ai_folder_path_str)
    if not page_id_to_display or not ai_folder_path.exists():
        st.info("Select a page to preview or run the process first.")
        return

    page_html_file = ai_folder_path / page_id_to_display / "index.html"
    if page_html_file.exists():
        print(f"[DASHBOARD_INFO] Displaying preview of: {page_html_file}") # For terminal log
        with open(page_html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        modified_html = modify_html_for_preview(html_content, page_id_to_display, ai_folder_path_str)
        st.markdown("---")
        st.subheader(f"Preview of `{page_id_to_display}/index.html`")
        st.markdown(
            "**Note:** Preview is experimental. Navigation between pages *within this preview* is enabled. "
            "External links open in a new tab. For the most accurate view, open the generated files "
            "from the output folder (e.g., `your_domain_ai/`) in your browser."
        )
        st.components.v1.html(modified_html, height=600, scrolling=True)
    else:
        print(f"[DASHBOARD_WARN] Could not find main page {page_html_file} to display.") # For terminal log
        st.warning(f"Could not find `index.html` for page `{page_id_to_display}` in `{ai_folder_path_str}`.")

def run_subprocess_and_log(command_array, step_key, step_name_for_ui):
    """Runs a subprocess, logs its output to UI and terminal."""
    update_step_status(step_key, "running", step_name_for_ui)
    print(f"\n[DASHBOARD_RUNNING_STEP] {step_name_for_ui}")
    print(f"[DASHBOARD_COMMAND] {' '.join(command_array)}")
    
    process_output_for_ui = ""
    try:
        process = subprocess.Popen(command_array, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        
        # Stream output
        for line in process.stdout:
            print(line, end='') # Print to terminal in real-time
            process_output_for_ui += line

        process.wait() # Wait for the process to complete

        # After process completion, update UI log in one go
        append_log_to_ui(process_output_for_ui)

        if process.returncode == 0:
            update_step_status(step_key, "completed", step_name_for_ui)
            print(f"[DASHBOARD_STEP_SUCCESS] {step_name_for_ui} completed.")
            return process.returncode, process_output_for_ui # Return stdout for parsing if needed
        else:
            update_step_status(step_key, "error", step_name_for_ui)
            print(f"[DASHBOARD_STEP_ERROR] {step_name_for_ui} failed with exit code {process.returncode}.")
            return process.returncode, process_output_for_ui

    except subprocess.TimeoutExpired:
        timeout_msg = f"{step_name_for_ui} process timed out."
        print(f"[DASHBOARD_STEP_ERROR] {timeout_msg}")
        append_log_to_ui(timeout_msg + "\n")
        update_step_status(step_key, "error", step_name_for_ui)
        return -1, timeout_msg # Use a distinct return code for timeout
    except Exception as e:
        error_msg = f"Exception during {step_name_for_ui}: {str(e)}"
        print(f"[DASHBOARD_STEP_ERROR] {error_msg}")
        append_log_to_ui(error_msg + "\n")
        update_step_status(step_key, "error", step_name_for_ui)
        return -2, error_msg # Use a distinct return code for other exceptions

def run_full_process(target_url):
    st.session_state.process_running = True
    clear_ui_logs()
    st.session_state.current_preview_page_id = None 
    st.session_state.ai_output_folder = None      

    print(f"\n[DASHBOARD_INFO] Starting website modernization for: {target_url}")
    append_log_to_ui(f"🚀 Starting website modernization for: {target_url}\n")

    # URL validation
    update_step_status("validate", "running", "URL Validation")
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        msg = "Invalid URL format - missing http:// or https://"
        print(f"[DASHBOARD_ERROR] {msg}")
        append_log_to_ui(msg + "\n")
        update_step_status("validate", "error", "URL Validation")
        st.error("Invalid URL. Please include http:// or https://")
        st.session_state.process_running = False
        return

    match = re.search(r"https?://([^/]+)", target_url)
    if not match:
        msg = "Could not parse domain from URL"
        print(f"[DASHBOARD_ERROR] {msg}")
        append_log_to_ui(msg + "\n")
        update_step_status("validate", "error", "URL Validation")
        st.error("Could not parse domain from URL.")
        st.session_state.process_running = False
        return
    
    domain_base = match.group(1).replace(':', '_')
    print(f"[DASHBOARD_INFO] Parsed domain: {domain_base}")
    append_log_to_ui(f"✅ Parsed domain: {domain_base}\n")
    update_step_status("validate", "completed", "URL Validation")

    # Step 1: Website Crawling
    crawl_cmd = [sys.executable, "crawl_site.py", target_url]
    crawl_return_code, crawl_output = run_subprocess_and_log(crawl_cmd, "crawl", "Website Crawling")
    
    site_folder = None
    if crawl_return_code == 0:
        # Parse output directory from crawl script's last line of stdout
        lines = crawl_output.strip().split('\n')
        if lines:
            last_line = lines[-1].strip() # Ensure no hidden chars
            # Check if last line is a directory path that seems plausible
            if os.path.isdir(last_line) and (domain_base.replace('.','_') in last_line or domain_base in last_line):
                site_folder = last_line
                print(f"[DASHBOARD_INFO] Crawl script reported output directory: {site_folder}")
                append_log_to_ui(f"Crawled site data saved in: {site_folder}\n")
        
        if not site_folder: # Fallback
            candidates = sorted(
                [d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith(domain_base.replace('.','_')) and not d.name.endswith("_ai")],
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            if candidates:
                site_folder = str(candidates[0])
                print(f"[DASHBOARD_INFO] Found candidate crawl output folder by search: {site_folder}")
                append_log_to_ui(f"Found crawled site data by search: {site_folder}\n")
        
        if not site_folder or not os.path.isdir(site_folder):
            msg = f"Crawl output folder not found for domain '{domain_base}'."
            print(f"[DASHBOARD_ERROR] {msg}")
            append_log_to_ui(msg + "\n")
            update_step_status("crawl", "error", "Website Crawling") # Mark as error if folder not found
            st.error(msg)
            st.session_state.process_running = False
            return
    else:
        st.error("Crawl process failed. Check logs in terminal and UI.")
        st.session_state.process_running = False
        return

    # Step 2: AI Processing
    remake_cmd = [sys.executable, "remake_site_with_ai.py", site_folder]
    ai_return_code, _ = run_subprocess_and_log(remake_cmd, "ai", "AI Processing")
    
    st.session_state.ai_output_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"

    if ai_return_code == 0:
        update_step_status("generate", "completed", "File Generation") # Assuming AI script handles file saving
        st.success(f"✅ Modernization complete! Output in: {st.session_state.ai_output_folder}")
        print(f"[DASHBOARD_SUCCESS] Modernization complete! Output in: {st.session_state.ai_output_folder}")
        
        # Set initial page for preview
        home_page_id = "home"
        available_pages_in_ai_folder = [
            d.name for d in Path(st.session_state.ai_output_folder).iterdir() 
            if d.is_dir() and (d / "index.html").exists()
        ]
        if home_page_id in available_pages_in_ai_folder:
            st.session_state.current_preview_page_id = home_page_id
        elif available_pages_in_ai_folder:
            st.session_state.current_preview_page_id = available_pages_in_ai_folder[0]
        else:
            print("[DASHBOARD_WARN] No pages found in AI output folder for preview.")
            st.warning("No pages found in the AI output folder to preview.")
    else:
        st.error("AI remake process failed. Check logs in terminal and UI.")
        print("[DASHBOARD_ERROR] AI remake process failed.")
        st.session_state.ai_output_folder = None # Clear if failed
    
    st.session_state.process_running = False
    st.rerun()

# --- UI Layout and Interaction ---
col1_main, col2_main = st.columns([3, 1])
with col1_main:
    if st.button("🚀 Crawl & Modernize Site", disabled=st.session_state.process_running, type="primary", use_container_width=True):
        if url_input and (url_input.startswith("http://") or url_input.startswith("https://")):
            run_full_process(url_input)
        else:
            st.warning("Please enter a valid website URL starting with http:// or https://")
with col2_main:
    if st.button("🗑️ Clear Logs & Reset", disabled=st.session_state.process_running, use_container_width=True):
        clear_ui_logs()
        st.session_state.current_preview_page_id = None
        st.session_state.ai_output_folder = None
        st.rerun()

# Display process status indicators
steps_config = [
    ("URL Validation", "validate"), ("Website Crawling", "crawl"),
    ("AI Processing", "ai"), ("File Generation", "generate")
]
if st.session_state.process_running or any(st.session_state.step_status.values()):
    st.markdown("---")
    st.subheader("⚙️ Process Overview")
    cols_status = st.columns(len(steps_config))
    for i, (step_name, step_key) in enumerate(steps_config):
        with cols_status[i]:
            status = st.session_state.step_status.get(step_key, "pending")
            icon = "⏳" # pending
            if status == "running": icon = "🔄"
            elif status == "completed": icon = "✅"
            elif status == "error": icon = "❌"
            st.metric(label=step_name, value=status.capitalize(), delta=icon, delta_color="off")

# --- Display Preview Section ---
if st.session_state.ai_output_folder and Path(st.session_state.ai_output_folder).exists():
    st.markdown("---")
    st.header("🌐 Site Preview")
    available_pages = sorted([
        d.name for d in Path(st.session_state.ai_output_folder).iterdir() 
        if d.is_dir() and (Path(st.session_state.ai_output_folder) / d.name / "index.html").exists()
    ])
    if not available_pages:
        st.warning("No previewable pages found in the AI output folder.")
    else:
        query_params = st.query_params
        if "preview_page" in query_params:
            navigated_page_id = query_params.get("preview_page") # .get handles if not set
            if isinstance(navigated_page_id, list): navigated_page_id = navigated_page_id[0]
            if navigated_page_id in available_pages and navigated_page_id != st.session_state.current_preview_page_id:
                st.session_state.current_preview_page_id = navigated_page_id
        
        if not st.session_state.current_preview_page_id or st.session_state.current_preview_page_id not in available_pages:
            st.session_state.current_preview_page_id = available_pages[0]
            
        selected_page_for_preview = st.selectbox(
            "🗂️ Navigate to page:",
            options=available_pages,
            index=available_pages.index(st.session_state.current_preview_page_id) if st.session_state.current_preview_page_id in available_pages else 0,
            key="page_selector_dropdown"
        )
        if selected_page_for_preview != st.session_state.current_preview_page_id:
            st.session_state.current_preview_page_id = selected_page_for_preview
            st.query_params["preview_page"] = selected_page_for_preview # Update URL for potential refresh/bookmark
            st.rerun()

        if st.session_state.current_preview_page_id:
            display_preview(st.session_state.current_preview_page_id, st.session_state.ai_output_folder)
elif st.session_state.process_running:
    pass # Already handled by "Process Overview" or spinner
elif not st.session_state.log_text : # Initial state before any run
    st.info("👆 Enter a website URL above and click '🚀 Crawl & Modernize Site' to get started!") 