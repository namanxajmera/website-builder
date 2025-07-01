import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import threading
import queue
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Website Modernizer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Session State Initialization ---
# (Ensures that these variables persist across reruns within a user's session)
if 'current_preview_file' not in st.session_state:
    st.session_state.current_preview_file = None
if 'ai_output_folder' not in st.session_state:
    st.session_state.ai_output_folder = None
if 'log_text' not in st.session_state:
    st.session_state.log_text = ""
if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'step_status' not in st.session_state: # Stores status like "pending", "running", "completed", "error"
    st.session_state.step_status = {}
if 'start_process_url' not in st.session_state:
    st.session_state.start_process_url = None
if 'realtime_logs' not in st.session_state:
    st.session_state.realtime_logs = ""
if 'current_step' not in st.session_state:
    st.session_state.current_step = None

# --- UI Styling and Constants ---
PROC_STEPS = {
    "validate": "URL Validation",
    "crawl": "Website Crawling",
    "ai": "AI Modernization",
    "generate": "File Generation"
}

# --- Logging and Status Update Functions ---
def append_log_to_ui(raw_message_from_subprocess):
    st.session_state.log_text += raw_message_from_subprocess
    # In a real-time scenario with long logs, you might need to manage log length
    # or use a more sophisticated logging component if Streamlit struggles.

def clear_ui_logs_and_state():
    st.session_state.log_text = ""
    st.session_state.step_status = {}
    st.session_state.current_preview_file = None
    st.session_state.ai_output_folder = None

def read_crawl_manifest(potential_site_folders):
    """Read crawl manifest to get site directory instead of parsing stdout"""
    for folder in potential_site_folders:
        if not os.path.isdir(folder):
            continue
        manifest_path = os.path.join(folder, "crawl_manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                if manifest.get("status") == "completed":
                    return manifest["output"]["site_dir"], manifest
            except Exception as e:
                print(f"[DASHBOARD_ERROR] Failed to read manifest {manifest_path}: {e}")
    return None, None

def update_step_status(step_key, status):
    st.session_state.step_status[step_key] = status

# --- HTML Preview Modification ---
def modify_html_for_preview(html_content, current_filename, ai_output_folder_path_str):
    ai_output_folder_path = Path(ai_output_folder_path_str)
    soup = BeautifulSoup(html_content, "html.parser")
    
    global_css_path = ai_output_folder_path / "global_styles.css"
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

    available_html_files = [
        f.name for f in ai_output_folder_path.iterdir() 
        if f.is_file() and f.name.endswith('.html')
    ]
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        parsed_href = urlparse(href)
        if parsed_href.scheme or parsed_href.netloc: # External link
            a_tag['target'] = '_blank'
            continue
        if href.endswith('.html') and href in available_html_files: # Internal link to another generated page
            a_tag['href'] = f"/?preview_file={href}" # Use query params for Streamlit navigation
            a_tag['target'] = '_self' # Ensure navigation happens in the main window
    return str(soup)

def display_preview(filename_to_display, ai_folder_path_str):
    ai_folder_path = Path(ai_folder_path_str)
    if not filename_to_display or not ai_folder_path.exists():
        st.info("Select an HTML file to preview or run the process first.")
        return

    html_file_path = ai_folder_path / filename_to_display
    if html_file_path.exists() and html_file_path.suffix == '.html':
        print(f"[DASHBOARD_INFO] Displaying preview of: {html_file_path}")
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        modified_html = modify_html_for_preview(html_content, filename_to_display, ai_folder_path_str)
        st.markdown("---")
        st.subheader(f"Preview of `{filename_to_display}`")
        st.markdown(
            "**Note:** Preview is experimental. Navigation between pages *within this preview* is enabled. "
            "External links open in a new tab. For the most accurate view, open the generated files "
            f"from the output folder (`{ai_folder_path.name}/`) in your browser."
        )
        st.components.v1.html(modified_html, height=600, scrolling=True)
    else:
        print(f"[DASHBOARD_WARN] Could not find HTML file {html_file_path} to display.")
        st.warning(f"Could not find HTML file `{filename_to_display}` in `{ai_folder_path_str}`.")

# --- Core Process Functions ---
def run_subprocess_and_log(command_array, step_key):
    step_name_for_ui = PROC_STEPS.get(step_key, step_key.capitalize())
    update_step_status(step_key, "running")
    st.session_state.current_step = step_key
    print(f"\n[DASHBOARD_RUNNING_STEP] {step_name_for_ui}") # For terminal log
    print(f"[DASHBOARD_COMMAND] {' '.join(command_array)}")
    
    process_output_for_ui_log = ""
    start_time = time.time()
    
    try:
        process = subprocess.Popen(command_array, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        for line in process.stdout:
            print(line, end='') # Print to terminal in real-time
            process_output_for_ui_log += line
            # Update session state with partial logs for real-time display
            st.session_state.realtime_logs = process_output_for_ui_log
        process.wait()
        
        append_log_to_ui(process_output_for_ui_log) # Append all output at once

        elapsed_time = time.time() - start_time
        if process.returncode == 0:
            update_step_status(step_key, "completed")
            print(f"[DASHBOARD_STEP_SUCCESS] {step_name_for_ui} completed in {elapsed_time:.2f}s.")
            return process.returncode, process_output_for_ui_log
        else:
            update_step_status(step_key, "error")
            print(f"[DASHBOARD_STEP_ERROR] {step_name_for_ui} failed (code {process.returncode}) in {elapsed_time:.2f}s.")
            return process.returncode, process_output_for_ui_log
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        timeout_msg = f"{step_name_for_ui} process timed out after {elapsed_time:.2f}s."
        print(f"[DASHBOARD_STEP_ERROR] {timeout_msg}")
        append_log_to_ui(timeout_msg + "\n")
        update_step_status(step_key, "error")
        return -1, timeout_msg
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Exception during {step_name_for_ui} ({elapsed_time:.2f}s): {str(e)}"
        print(f"[DASHBOARD_STEP_ERROR] {error_msg}")
        append_log_to_ui(error_msg + "\n")
        update_step_status(step_key, "error")
        return -2, error_msg

def run_full_process(target_url):
    st.session_state.process_running = True
    clear_ui_logs_and_state() # Resets logs and status for new run
    st.session_state.process_running = True # Set back to true after clear

    print(f"\n[DASHBOARD_INFO] Full process started for: {target_url}")
    append_log_to_ui(f"🚀 Initializing modernization for: {target_url}\n")

    # Validate URL
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        msg = "Invalid URL: Must start with http:// or https://"
        update_step_status("validate", "error")
        st.error(msg); print(f"[DASHBOARD_ERROR] {msg}"); append_log_to_ui(msg + "\n")
        st.session_state.process_running = False; return
    match = re.search(r"https?://([^/]+)", target_url)
    if not match:
        msg = "Could not parse domain from URL."
        update_step_status("validate", "error")
        st.error(msg); print(f"[DASHBOARD_ERROR] {msg}"); append_log_to_ui(msg + "\n")
        st.session_state.process_running = False; return
    domain_base = match.group(1).replace(':', '_')
    update_step_status("validate", "completed")
    print(f"[DASHBOARD_INFO] Domain parsed: {domain_base}")

    # Crawl
    crawl_cmd = [sys.executable, "crawl_site.py", target_url]
    crawl_return_code, crawl_output = run_subprocess_and_log(crawl_cmd, "crawl")
    site_folder = None
    if crawl_return_code == 0:
        # Try manifest-based approach first (reliable)
        potential_folders = sorted([d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith(domain_base.replace('.','_')) and not d.name.endswith("_ai")], key=lambda p: p.stat().st_mtime, reverse=True)
        site_folder, manifest = read_crawl_manifest(potential_folders)
        
        if site_folder:
            print(f"[DASHBOARD_INFO] Site folder found via manifest: {site_folder} (crawled {manifest['crawl_info']['pages_crawled']} pages)")
        else:
            # Legacy fallback: parse stdout (for backward compatibility)
            lines = crawl_output.strip().split('\n')
            if lines:
                last_line = lines[-1].strip()
                if os.path.isdir(last_line) and (domain_base.replace('.','_') in last_line or domain_base in last_line):
                    site_folder = last_line
                    print(f"[DASHBOARD_WARN] Using legacy stdout parsing for site folder: {site_folder}")
            
            # Final fallback: directory search
            if not site_folder and potential_folders:
                site_folder = str(potential_folders[0])
                print(f"[DASHBOARD_WARN] Using directory search fallback: {site_folder}")
        
        if not site_folder or not os.path.isdir(site_folder):
            msg = f"Crawl output folder not found for '{domain_base}'."
            update_step_status("crawl", "error"); st.error(msg); print(f"[DASHBOARD_ERROR] {msg}"); append_log_to_ui(msg + "\n")
            st.session_state.process_running = False; return
        print(f"[DASHBOARD_INFO] Crawled data in: {site_folder}")
    else:
        st.error("Crawl process failed. Check logs."); st.session_state.process_running = False; return

    # AI Remake
    remake_cmd = [sys.executable, "remake_site_with_ai.py", site_folder, 
                  "--model", st.session_state.get("ai_model", "gemini-2.5-flash-preview-05-20"),
                  "--temperature", str(st.session_state.get("ai_temperature", 0.5))]
    ai_return_code, _ = run_subprocess_and_log(remake_cmd, "ai")
    st.session_state.ai_output_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"

    if ai_return_code == 0:
        update_step_status("generate", "completed")
        st.success(f"🎉 Modernization complete! Output in: {st.session_state.ai_output_folder}")
        print(f"[DASHBOARD_SUCCESS] Modernization complete! Output: {st.session_state.ai_output_folder}")
        
        # Display AI structural decision if available
        decision_file = os.path.join(st.session_state.ai_output_folder, "ai_decision.txt")
        if os.path.exists(decision_file):
            try:
                with open(decision_file, "r", encoding="utf-8") as f:
                    ai_decision = f.read().strip()
                if ai_decision:
                    st.info(f"🧠 **AI Structural Decision:** {ai_decision}")
            except Exception as e:
                print(f"[DASHBOARD_WARN] Failed to read AI decision file: {e}")
        
        available_html_files = [f.name for f in Path(st.session_state.ai_output_folder).iterdir() if f.is_file() and f.name.endswith('.html')]
        if "index.html" in available_html_files: st.session_state.current_preview_file = "index.html"
        elif available_html_files: st.session_state.current_preview_file = available_html_files[0]
        else: st.warning("No HTML files found in AI output for preview.")
    else:
        st.error("AI modernization process failed. Check logs."); st.session_state.ai_output_folder = None
    
    st.session_state.process_running = False
    st.rerun()

# --- UI Layout ---

# Custom CSS for header/footer and enhanced styling
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 1rem;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }
    .main-content {
        flex: 1;
    }
    .status-card {
        text-align: center;
        padding: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
        background-color: #f9f9f9;
        margin: 0.25rem;
        transition: all 0.3s ease;
    }
    .status-card:hover {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .status-running {
        border-color: #ffc107;
        background-color: #fff3cd;
    }
    .status-completed {
        border-color: #28a745;
        background-color: #d4edda;
    }
    .status-error {
        border-color: #dc3545;
        background-color: #f8d7da;
    }
</style>
""", unsafe_allow_html=True)

# Main application content area
main_content_area = st.container()

with main_content_area:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Input Section
    col_input, col_run, col_reset = st.columns([4, 2, 1])
    
    with col_input:
        url_input_val = st.text_input(
            "Target Website URL", 
            "https://example.com", 
            key="url_input_main",
            help="Enter the full URL (e.g., https://www.example.com) of the website you want to modernize.",
            label_visibility="collapsed"
        )
        
        # AI Configuration Options
        col_model, col_temp = st.columns([2, 1])
        with col_model:
            ai_model = st.selectbox(
                "AI Model",
                ["gemini-2.5-flash-preview-05-20", "gemini-1.5-pro-latest"],
                index=0,
                help="Select the Gemini model: Flash for speed, Pro for comprehensive analysis"
            )
        with col_temp:
            ai_temperature = st.slider(
                "Creativity",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Higher values make AI output more creative and varied"
            )
    
    with col_run:
        if st.button("🚀 Modernize Website!", type="primary", use_container_width=True, disabled=st.session_state.process_running):
            if url_input_val and (url_input_val.startswith("http://") or url_input_val.startswith("https://")):
                st.session_state.start_process_url = url_input_val
                st.session_state.ai_model = ai_model
                st.session_state.ai_temperature = ai_temperature
                st.session_state.process_running = True
                st.rerun()
            else:
                st.error("Please enter a valid website URL starting with http:// or https://")
    
    with col_reset:
        if st.button("🗑️ Reset", use_container_width=True, disabled=st.session_state.process_running):
            clear_ui_logs_and_state()
            st.rerun()

    # Check if a process should be started
    if st.session_state.start_process_url:
        url_to_process = st.session_state.start_process_url
        st.session_state.start_process_url = None  # Clear the flag
        run_full_process(url_to_process)

    # Preview Section
    if st.session_state.ai_output_folder and Path(st.session_state.ai_output_folder).exists():
        st.markdown("---")
        st.subheader("🖼️ Generated Site Preview")
        
        ai_output_path = Path(st.session_state.ai_output_folder)
        available_html_files = sorted([f.name for f in ai_output_path.iterdir() if f.is_file() and f.name.endswith('.html')])

        if not available_html_files:
            st.warning(f"No HTML files found in the output directory: {st.session_state.ai_output_folder}")
        else:
            query_params = st.query_params
            if "preview_file" in query_params:
                navigated_file = query_params.get("preview_file")
                if isinstance(navigated_file, list): navigated_file = navigated_file[0]
                if navigated_file in available_html_files and navigated_file != st.session_state.current_preview_file:
                    st.session_state.current_preview_file = navigated_file
            
            if not st.session_state.current_preview_file or st.session_state.current_preview_file not in available_html_files:
                st.session_state.current_preview_file = "index.html" if "index.html" in available_html_files else available_html_files[0]
            
            selected_file_for_preview = st.selectbox(
                "Select page to preview:",
                options=available_html_files,
                index=available_html_files.index(st.session_state.current_preview_file) if st.session_state.current_preview_file in available_html_files else 0,
                key="file_selector_dropdown_preview"
            )
            if selected_file_for_preview != st.session_state.current_preview_file:
                st.session_state.current_preview_file = selected_file_for_preview
                st.query_params["preview_file"] = selected_file_for_preview 
                st.rerun()

            if st.session_state.current_preview_file:
                display_preview(st.session_state.current_preview_file, st.session_state.ai_output_folder)

    st.markdown('</div>', unsafe_allow_html=True)