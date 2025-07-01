import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import re
import time
import json
import webbrowser

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Website Modernizer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Session State Initialization ---
if 'current_preview_file' not in st.session_state:
    st.session_state.current_preview_file = None
if 'ai_output_folder' not in st.session_state:
    st.session_state.ai_output_folder = None
if 'log_text' not in st.session_state:
    st.session_state.log_text = ""
if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'step_status' not in st.session_state:
    st.session_state.step_status = {}
if 'start_process_url' not in st.session_state:
    st.session_state.start_process_url = None
if 'realtime_logs' not in st.session_state:
    st.session_state.realtime_logs = ""
if 'current_step' not in st.session_state:
    st.session_state.current_step = None
if 'transformation_complete' not in st.session_state:
    st.session_state.transformation_complete = False

# --- Process Steps ---
PROC_STEPS = {
    "validate": "URL Validation",
    "crawl": "Website Crawling", 
    "ai": "AI Modernization",
    "generate": "File Generation"
}

# --- Utility Functions ---
def clear_ui_logs_and_state():
    st.session_state.log_text = ""
    st.session_state.step_status = {}
    st.session_state.current_preview_file = None
    st.session_state.ai_output_folder = None
    st.session_state.transformation_complete = False

def read_crawl_manifest(potential_site_folders):
    """Read crawl manifest to get site directory"""
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

def run_subprocess_and_log(command_array, step_key):
    step_name_for_ui = PROC_STEPS.get(step_key, step_key.capitalize())
    update_step_status(step_key, "running")
    st.session_state.current_step = step_key
    print(f"\n[DASHBOARD_RUNNING_STEP] {step_name_for_ui}")
    print(f"[DASHBOARD_COMMAND] {' '.join(command_array)}")
    
    process_output_for_ui_log = ""
    start_time = time.time()
    
    try:
        process = subprocess.Popen(command_array, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        for line in process.stdout:
            print(line, end='')
            process_output_for_ui_log += line
            st.session_state.realtime_logs = process_output_for_ui_log
        process.wait()
        
        st.session_state.log_text += process_output_for_ui_log

        elapsed_time = time.time() - start_time
        if process.returncode == 0:
            update_step_status(step_key, "completed")
            print(f"[DASHBOARD_STEP_SUCCESS] {step_name_for_ui} completed in {elapsed_time:.2f}s.")
            return process.returncode, process_output_for_ui_log
        else:
            update_step_status(step_key, "error")
            print(f"[DASHBOARD_STEP_ERROR] {step_name_for_ui} failed (code {process.returncode}) in {elapsed_time:.2f}s.")
            return process.returncode, process_output_for_ui_log
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Exception during {step_name_for_ui} ({elapsed_time:.2f}s): {str(e)}"
        print(f"[DASHBOARD_STEP_ERROR] {error_msg}")
        st.session_state.log_text += error_msg + "\n"
        update_step_status(step_key, "error")
        return -2, error_msg

def run_full_process(target_url):
    st.session_state.process_running = True
    clear_ui_logs_and_state()
    st.session_state.process_running = True
    st.session_state.transformation_complete = False

    print(f"\n[DASHBOARD_INFO] Full process started for: {target_url}")
    st.session_state.log_text += f"🚀 Initializing modernization for: {target_url}\n"

    # Validate URL
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        msg = "Invalid URL: Must start with http:// or https://"
        update_step_status("validate", "error")
        st.error(msg)
        st.session_state.process_running = False
        return
    
    match = re.search(r"https?://([^/]+)", target_url)
    if not match:
        msg = "Could not parse domain from URL."
        update_step_status("validate", "error")
        st.error(msg)
        st.session_state.process_running = False
        return
    
    domain_base = match.group(1).replace(':', '_')
    update_step_status("validate", "completed")

    # Crawl
    crawl_cmd = [sys.executable, "crawl_site.py", target_url]
    crawl_return_code, crawl_output = run_subprocess_and_log(crawl_cmd, "crawl")
    site_folder = None
    
    if crawl_return_code == 0:
        potential_folders = sorted([d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith(domain_base.replace('.','_')) and not d.name.endswith("_ai")], key=lambda p: p.stat().st_mtime, reverse=True)
        site_folder, manifest = read_crawl_manifest(potential_folders)
        
        if site_folder:
            print(f"[DASHBOARD_INFO] Site folder found via manifest: {site_folder} (crawled {manifest['crawl_info']['pages_crawled']} pages)")
        else:
            lines = crawl_output.strip().split('\n')
            if lines:
                last_line = lines[-1].strip()
                if os.path.isdir(last_line) and (domain_base.replace('.','_') in last_line or domain_base in last_line):
                    site_folder = last_line
            
            if not site_folder and potential_folders:
                site_folder = str(potential_folders[0])
        
        if not site_folder or not os.path.isdir(site_folder):
            msg = f"Crawl output folder not found for '{domain_base}'."
            update_step_status("crawl", "error")
            st.error(msg)
            st.session_state.process_running = False
            return
    else:
        st.error("Crawl process failed. Check logs.")
        st.session_state.process_running = False
        return

    # AI Remake
    remake_cmd = [sys.executable, "remake_site_with_ai.py", site_folder, 
                  "--model", st.session_state.get("ai_model", "gemini-2.5-flash"),
                  "--temperature", str(st.session_state.get("ai_temperature", 0.5))]
    ai_return_code, _ = run_subprocess_and_log(remake_cmd, "ai")
    st.session_state.ai_output_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"

    if ai_return_code == 0:
        update_step_status("generate", "completed")
        st.session_state.transformation_complete = True
        st.success(f"🎉 Modernization complete! Output in: {st.session_state.ai_output_folder}")
        
        # Display AI decision if available
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
        if "index.html" in available_html_files:
            st.session_state.current_preview_file = "index.html"
        elif available_html_files:
            st.session_state.current_preview_file = available_html_files[0]
    else:
        st.error("AI modernization process failed. Check logs.")
        st.session_state.ai_output_folder = None
    
    st.session_state.process_running = False
    st.rerun()

# --- Modern UI Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main > div {
        padding-top: 2rem;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 400;
        opacity: 0.9;
        max-width: 500px;
        margin: 0 auto;
        line-height: 1.4;
    }
    
    .process-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #f1f5f9;
        transition: all 0.3s ease;
    }
    
    .process-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        position: relative;
    }
    
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    
    .step-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: white;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 2;
    }
    
    .step-pending { background: #e2e8f0; color: #64748b; }
    .step-running { background: #fbbf24; color: white; animation: pulse 2s infinite; }
    .step-completed { background: #10b981; color: white; }
    .step-error { background: #ef4444; color: white; }
    
    .step-line {
        position: absolute;
        top: 30px;
        left: 50%;
        right: -50%;
        height: 3px;
        background: #e2e8f0;
        z-index: 1;
    }
    
    .step-line.completed {
        background: #10b981;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .results-section {
        background: #f8fafc;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .action-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0.5rem;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(102, 126, 234, 0.4);
    }
    
    .secondary-button {
        background: white;
        color: #667eea;
        border: 2px solid #667eea;
    }
    
    .secondary-button:hover {
        background: #667eea;
        color: white;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #64748b;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- Hero Section ---
st.markdown("""
<div class="hero-section">
    <div class="hero-title">AI Website Modernizer</div>
    <div class="hero-subtitle">Transform websites with AI-powered modernization</div>
</div>
""", unsafe_allow_html=True)

# --- Main Input Section ---
with st.container():
    st.markdown('<div class="process-card">', unsafe_allow_html=True)
    st.subheader("🎯 Website Transformation")
    
    # URL Input
    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input(
            "Website URL to Modernize",
            placeholder="https://your-website.com",
            help="Enter the full URL of the website you want to transform"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        transform_button = st.button(
            "🚀 Transform Website", 
            type="primary", 
            use_container_width=True,
            disabled=st.session_state.process_running
        )
    
    # Advanced Configuration (Collapsible)
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            ai_model = st.selectbox(
                "AI Model",
                ["gemini-2.5-flash", "gemini-2.5-pro"],
                help="Flash: Faster processing | Pro: More comprehensive analysis"
            )
        with col2:
            ai_temperature = st.slider(
                "AI Creativity Level",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Higher values = more creative and varied output"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Simple Status Display ---
if st.session_state.process_running:
    if st.session_state.current_step:
        current_step_name = PROC_STEPS.get(st.session_state.current_step, st.session_state.current_step)
        st.info(f"⏳ {current_step_name} in progress...")
    else:
        st.info("⏳ Processing...")
elif any(status == "error" for status in st.session_state.step_status.values()):
    st.error("❌ Transformation failed - check logs below")

# --- Results Section ---
if st.session_state.transformation_complete and st.session_state.ai_output_folder:
    ai_output_path = Path(st.session_state.ai_output_folder)
    if ai_output_path.exists():
        available_html_files = [f for f in ai_output_path.iterdir() if f.is_file() and f.name.endswith('.html')]
        
        if available_html_files:
            index_file = ai_output_path / "index.html"
            if index_file.exists():
                st.success("✅ Transformation complete!")
                
                # Show the file path for manual opening
                st.info(f"📁 Generated website location: `{index_file.absolute()}`")
                
                # Button to open website
                if st.button("🌐 Open Generated Website", key="open_website", type="primary", help="Opens the generated website in your default browser"):
                    import platform
                    import subprocess
                    system = platform.system()
                    try:
                        if system == "Darwin":  # macOS
                            subprocess.run(["open", str(index_file.absolute())])
                        elif system == "Windows":
                            subprocess.run(["start", str(index_file.absolute())], shell=True)
                        else:  # Linux
                            subprocess.run(["xdg-open", str(index_file.absolute())])
                        st.success("🚀 Website opened in your browser!")
                    except Exception as e:
                        st.error(f"Could not open website automatically. Error: {e}")
                        st.markdown(f"**Manual option:** Copy this path and open it in your browser: `file://{index_file.absolute()}`")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 Transform Another Website", key="new_transform"):
                        clear_ui_logs_and_state()
                        st.rerun()
                with col2:
                    if st.button("📁 Open Output Folder", key="open_folder"):
                        import platform
                        system = platform.system()
                        try:
                            if system == "Darwin":  # macOS
                                os.system(f'open "{ai_output_path.absolute()}"')
                            elif system == "Windows":
                                os.system(f'explorer "{ai_output_path.absolute()}"')
                            else:  # Linux
                                os.system(f'xdg-open "{ai_output_path.absolute()}"')
                            st.success("Folder opened!")
                        except Exception as e:
                            st.error(f"Could not open folder: {e}")
            else:
                st.error("index.html not found in generated output")

# --- Process Handler ---
if transform_button and url_input:
    if url_input.startswith("http://") or url_input.startswith("https://"):
        st.session_state.start_process_url = url_input
        st.session_state.ai_model = ai_model
        st.session_state.ai_temperature = ai_temperature
        st.session_state.process_running = True
        st.rerun()
    else:
        st.error("❌ Please enter a valid URL starting with http:// or https://")

if st.session_state.start_process_url:
    url_to_process = st.session_state.start_process_url
    st.session_state.start_process_url = None
    run_full_process(url_to_process)

# --- Advanced Logs (Optional) ---
if st.session_state.log_text and st.checkbox("🔧 Show detailed logs", help="View technical logs for debugging"):
    with st.expander("Technical Logs", expanded=False):
        st.code(st.session_state.log_text, language="text")