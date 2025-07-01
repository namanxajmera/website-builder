# 🔌 AI Website Modernizer - API Documentation

---
**FILE**: API.md  
**PURPOSE**: Component APIs, function references, and usage examples  
**AUDIENCE**: engineers  
**CODE_REFERENCES**: 38  
---

## Overview

This document provides comprehensive API documentation for the AI Website Modernizer components, including function signatures, parameters, return values, and usage examples with direct code references.

## 📦 Module APIs

### 🕷️ Web Crawler API ([`crawl_site.py`](./crawl_site.py))

#### Core Functions

##### `setup_driver() -> webdriver.Chrome`
**Location**: [`crawl_site.py:68-85`](./crawl_site.py#L68-L85)

Initializes Chrome WebDriver with headless configuration and timeout settings.

```python
def setup_driver():
    """Initialize Chrome WebDriver with security and performance settings."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)  # 30 seconds timeout
    return driver
```

**Returns**: Configured Chrome WebDriver instance  
**Raises**: `SystemExit` if ChromeDriver initialization fails

---

##### `is_safe_url(url: str) -> bool`
**Location**: [`crawl_site.py:29-66`](./crawl_site.py#L29-L66)

Validates URL safety to prevent SSRF (Server-Side Request Forgery) attacks.

```python
def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks by checking if target IP is public"""
    parsed = urlparse(url)
    hostname = parsed.hostname
    ip_str = socket.gethostbyname(hostname)
    ip_obj = ipaddress.ip_address(ip_str)
    
    # Block private/reserved IP ranges
    return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved)
```

**Parameters**:
- `url` (str): URL to validate

**Returns**: `True` if URL is safe to crawl, `False` otherwise  
**Security**: Blocks private networks, loopback, and reserved IP ranges

---

##### `get_page_content(driver, url: str) -> Optional[Tuple[str, set, str, set, list]]`
**Location**: [`crawl_site.py:99-157`](./crawl_site.py#L99-L157)

Extracts comprehensive content from a web page including HTML, images, text, and CSS.

```python
def get_page_content(driver, url: str):
    """Extract all content from a web page for AI processing."""
    if not is_safe_url(url):
        return None, None, None, None
    
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract images
    images = {urljoin(url, img.get('src')) for img in soup.find_all('img') if img.get('src')}
    
    # Extract CSS files  
    css_files = {urljoin(url, link.get('href')) for link in soup.find_all('link', rel='stylesheet') if link.get('href')}
    
    # Extract text content
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text(separator='\n', strip=True)
    
    return html, images, text, css_files, inline_styles
```

**Parameters**:
- `driver`: Selenium WebDriver instance
- `url` (str): URL to extract content from

**Returns**: Tuple of (html, images, text, css_files, inline_styles) or None values on failure  
**Timeout**: 30 seconds via WebDriver configuration

---

##### `save_page_data(site_dir: str, folder_name: str, url: str, html: str, text: str, images: set, css_files: set, inline_styles: list) -> bool`
**Location**: [`crawl_site.py:217-267`](./crawl_site.py#L217-L267)

Saves extracted page content to structured file system.

```python
def save_page_data(site_dir, folder_name, url, html, text, images, css_files, inline_styles):
    """Save all extracted page data to organized file structure."""
    page_dir = os.path.join(site_dir, folder_name)
    os.makedirs(page_dir, exist_ok=True)
    
    # Save individual content files
    with open(os.path.join(page_dir, URL_FILENAME), "w", encoding="utf-8") as f:
        f.write(url)
    # ... additional file saves
```

**Parameters**:
- `site_dir` (str): Base directory for site data
- `folder_name` (str): Subdirectory name for this page
- `url` (str): Original page URL
- `html` (str): Page HTML content
- `text` (str): Extracted text content
- `images` (set): Set of image URLs
- `css_files` (set): Set of CSS file URLs
- `inline_styles` (list): List of inline style blocks

**Returns**: `True` on successful save, `False` on error  
**Files Created**: `url.txt`, `page.html`, `copy.txt`, `images.txt`, `css.txt`

---

#### File Constants
**Location**: [`crawl_site.py:22-27`](./crawl_site.py#L22-L27)

```python
COPY_FILENAME = "copy.txt"      # Extracted text content
CSS_FILENAME = "css.txt"        # CSS styles and references  
HTML_FILENAME = "page.html"     # Original HTML content
IMAGES_FILENAME = "images.txt"  # Image URL list
URL_FILENAME = "url.txt"        # Page URL
```

#### Configuration Constants
**Location**: [`crawl_site.py:19-20`](./crawl_site.py#L19-L20)

```python
DEFAULT_MAX_PAGES = 20          # Maximum pages to crawl
DEFAULT_CRAWL_DEPTH = 2         # Maximum crawling depth
```

---

### 🤖 AI Processing API ([`remake_site_with_ai.py`](./remake_site_with_ai.py))

#### Core Functions

##### `load_gemini_api_key() -> Optional[str]`
**Location**: [`remake_site_with_ai.py:20-30`](./remake_site_with_ai.py#L20-L30)

Securely loads Google Gemini API key from environment variables.

```python
def load_gemini_api_key() -> Optional[str]:
    """Load Gemini API key from environment variable."""
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if api_key:
        cprint("[SUCCESS] API key loaded from environment variable", "green")
        return api_key
    else:
        cprint("[ERROR] GOOGLE_GEMINI_API_KEY environment variable not set!", "red")
        return None
```

**Returns**: API key string or `None` if not configured  
**Environment**: Requires `GOOGLE_GEMINI_API_KEY` environment variable

---

##### `gemini_generate_entire_site(all_pages_data_str: str, model_name: str = "gemini-2.5-flash-preview-05-20", temperature: float = 0.5) -> Optional[Dict[str, Any]]`
**Location**: [`remake_site_with_ai.py:32-165`](./remake_site_with_ai.py#L32-L165)

Main AI processing function that generates modernized website from crawled content.

```python
def gemini_generate_entire_site(all_pages_data_str: str, model_name: str, temperature: float):
    """Generate entire modernized website using Google Gemini AI."""
    # Load prompt template
    prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "rebuild_prompt.txt")
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Configure Gemini API
    genai.configure(api_key=api_key)
    model_instance = genai.GenerativeModel(model_name=model_name)
    
    # Generate content
    response = model_instance.generate_content(
        contents=prompt,
        generation_config=genai.types.GenerationConfig(temperature=temperature)
    )
    
    # Parse and validate JSON response
    ai_json_response = json.loads(cleaned_text)
    return ai_json_response
```

**Parameters**:
- `all_pages_data_str` (str): XML-formatted string containing all crawled page data
- `model_name` (str): Gemini model identifier (default: "gemini-2.5-flash-preview-05-20")
- `temperature` (float): AI creativity setting 0.0-1.0 (default: 0.5)

**Returns**: Dictionary with keys:
- `site_structure_decision` (str): AI's structural reasoning
- `global_css` (str): Generated CSS stylesheet
- `html_files` (dict): Mapping of filenames to HTML content

**Models Available**:
- `gemini-2.5-flash-preview-05-20`: Fast, efficient processing
- `gemini-1.5-pro-latest`: Comprehensive analysis, larger context

---

#### AI Response Structure

The AI processing returns a structured JSON response:

```json
{
  "site_structure_decision": "Single-page website chosen for concise content...",
  "global_css": "/* Modern CSS styles... */",
  "html_files": {
    "index.html": "<!DOCTYPE html>...",
    "about.html": "<!DOCTYPE html>..."
  }
}
```

**Validation**: [`remake_site_with_ai.py:126-136`](./remake_site_with_ai.py#L126-L136)
```python
required_keys = ["site_structure_decision", "global_css", "html_files"]
if not all(key in ai_response for key in required_keys):
    raise ValueError("Missing required keys in response")
```

---

### 📊 Dashboard API ([`dashboard.py`](./dashboard.py))

#### Core Functions

##### `run_full_process(target_url: str) -> None`
**Location**: [`dashboard.py:184-272`](./dashboard.py#L184-L272)

Orchestrates the complete website modernization pipeline.

```python
def run_full_process(target_url):
    """Execute complete website transformation pipeline."""
    st.session_state.process_running = True
    
    # Validate URL
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        update_step_status("validate", "error")
        return
    
    # Execute crawling
    crawl_cmd = [sys.executable, "crawl_site.py", target_url]
    crawl_return_code, crawl_output = run_subprocess_and_log(crawl_cmd, "crawl")
    
    # Execute AI processing
    remake_cmd = [sys.executable, "remake_site_with_ai.py", site_folder]
    ai_return_code, _ = run_subprocess_and_log(remake_cmd, "ai")
    
    st.session_state.process_running = False
```

**Parameters**:
- `target_url` (str): Website URL to modernize

**Side Effects**:
- Updates `st.session_state` for UI tracking
- Creates subprocess for each pipeline stage
- Generates output files in filesystem

---

##### `run_subprocess_and_log(command_array: list, step_key: str) -> Tuple[int, str]`
**Location**: [`dashboard.py:139-182`](./dashboard.py#L139-L182)

Executes subprocess with real-time logging and progress tracking.

```python
def run_subprocess_and_log(command_array, step_key):
    """Execute subprocess with real-time output capture."""
    update_step_status(step_key, "running")
    
    process = subprocess.Popen(
        command_array, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        bufsize=1
    )
    
    for line in process.stdout:
        print(line, end='')  # Real-time terminal output
        st.session_state.realtime_logs += line
    
    return process.returncode, process_output
```

**Parameters**:
- `command_array` (list): Command and arguments to execute
- `step_key` (str): Pipeline step identifier for tracking

**Returns**: Tuple of (return_code, output_text)  
**Status Updates**: Updates session state for UI progress indication

---

##### `display_preview(filename_to_display: str, ai_folder_path_str: str) -> None`
**Location**: [`dashboard.py:113-136`](./dashboard.py#L113-L136)

Renders HTML preview with navigation and styling modifications.

```python
def display_preview(filename_to_display, ai_folder_path_str):
    """Display HTML preview with enhanced navigation."""
    html_file_path = Path(ai_folder_path_str) / filename_to_display
    
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    modified_html = modify_html_for_preview(html_content, filename_to_display, ai_folder_path_str)
    st.components.v1.html(modified_html, height=600, scrolling=True)
```

**Parameters**:
- `filename_to_display` (str): HTML filename to preview
- `ai_folder_path_str` (str): Path to AI-generated website folder

**Features**:
- CSS integration from `global_styles.css`
- Internal link navigation support
- External link handling (opens in new tab)

---

#### Session State Management
**Location**: [`dashboard.py:24-39`](./dashboard.py#L24-L39)

```python
# Persistent state variables
if 'current_preview_file' not in st.session_state:
    st.session_state.current_preview_file = None
if 'ai_output_folder' not in st.session_state:
    st.session_state.ai_output_folder = None
if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'step_status' not in st.session_state:
    st.session_state.step_status = {}
```

**State Variables**:
- `current_preview_file`: Currently displayed HTML file
- `ai_output_folder`: Path to generated website
- `process_running`: Pipeline execution status
- `step_status`: Individual step completion tracking
- `log_text`: Accumulated log output
- `realtime_logs`: Live subprocess output

---

## 🔧 Configuration APIs

### Environment Variables

```bash
# Required
GOOGLE_GEMINI_API_KEY=your-api-key-here

# Optional  
DEBUG_MODE=1                    # Enable verbose logging
```

### Command Line Interfaces

#### Crawler CLI
**Usage**: [`crawl_site.py:270-277`](./crawl_site.py#L270-L277)

```bash
python crawl_site.py <url> [options]

Options:
  --max_pages INT    Maximum pages to crawl (default: 20)
  --depth INT        Maximum crawl depth (default: 2)
```

#### AI Processor CLI  
**Usage**: [`remake_site_with_ai.py:168-173`](./remake_site_with_ai.py#L168-L173)

```bash
python remake_site_with_ai.py <site_folder> [options]

Options:
  --model TEXT       Gemini model name (default: gemini-2.5-flash-preview-05-20)
  --temperature FLOAT AI creativity 0.0-1.0 (default: 0.5)
```

---

## 🔒 Security APIs

### URL Validation
**SSRF Protection**: [`is_safe_url()`](./crawl_site.py#L29-L66)
- Validates against private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Blocks loopback addresses (127.0.0.0/8)
- Prevents access to link-local addresses (169.254.0.0/16)

### Path Traversal Prevention
**Filename Validation**: [`remake_site_with_ai.py:372-387`](./remake_site_with_ai.py#L372-L387)

```python
# Security validation for AI-generated filenames
normalized_filename = os.path.normpath(filename)
if (normalized_filename != filename or 
    ".." in normalized_filename or 
    "/" in normalized_filename or "\\" in normalized_filename):
    # Block potentially unsafe filename
```

---

## 📊 Data Format APIs

### Crawl Manifest Structure
**Generated by**: [`crawl_site.py:386-412`](./crawl_site.py#L386-L412)

```json
{
  "version": "1.0",
  "timestamp": "2024-01-01T12:00:00",
  "crawl_info": {
    "target_url": "https://example.com",
    "base_netloc": "example.com", 
    "max_pages": 20,
    "crawl_depth": 2,
    "pages_crawled": 5
  },
  "output": {
    "site_dir": "example_com",
    "crawled_pages": ["https://example.com", "https://example.com/about"]
  },
  "status": "completed"
}
```

### Page Data XML Format
**Used by**: [`remake_site_with_ai.py:296-302`](./remake_site_with_ai.py#L296-L302)

```xml
<page id="home">
  <url><![CDATA[https://example.com]]></url>
  <original_html><![CDATA[<!DOCTYPE html>...]]></original_html>
  <original_css><![CDATA[/* CSS content */]]></original_css>
  <original_copy><![CDATA[Page text content]]></original_copy>
  <image_urls><![CDATA[https://example.com/image1.jpg]]></image_urls>
</page>
```

---

## 🚀 Usage Examples

### Programmatic Crawling

```python
from crawl_site import setup_driver, get_page_content, save_page_data

# Initialize crawler
driver = setup_driver()

# Extract content
html, images, text, css_files, inline_styles = get_page_content(driver, "https://example.com")

# Save to filesystem
success = save_page_data("output_dir", "home", "https://example.com", 
                        html, text, images, css_files, inline_styles)

driver.quit()
```

### AI Processing Integration

```python
from remake_site_with_ai import gemini_generate_entire_site

# Prepare page data
page_data_xml = "<page id='home'>...</page>"

# Generate modernized site
result = gemini_generate_entire_site(
    page_data_xml, 
    model_name="gemini-2.5-flash-preview-05-20",
    temperature=0.7
)

if result:
    print(f"Generated {len(result['html_files'])} pages")
    print(f"CSS size: {len(result['global_css'])} characters")
```

### Dashboard Integration

```python
import streamlit as st
from dashboard import run_full_process

# Streamlit app
st.title("AI Website Modernizer")
url = st.text_input("Website URL")

if st.button("Modernize"):
    run_full_process(url)
    
    if st.session_state.ai_output_folder:
        st.success("Modernization complete!")
```

---

## 🔍 Error Handling

### Exception Types

| Exception | Location | Description |
|-----------|----------|-------------|
| `TimeoutException` | [`crawl_site.py:110`](./crawl_site.py#L110) | Page load timeout |
| `json.JSONDecodeError` | [`remake_site_with_ai.py:144`](./remake_site_with_ai.py#L144) | AI response parsing error |
| `ValueError` | [`remake_site_with_ai.py:127`](./remake_site_with_ai.py#L127) | Invalid AI response structure |
| `socket.gaierror` | [`crawl_site.py:60`](./crawl_site.py#L60) | DNS resolution failure |

### Error Recovery Patterns

```python
# Timeout handling with graceful degradation
try:
    driver.get(url)
except TimeoutException:
    cprint(f"Page load timeout for {url}", "red")
    return None, None, None, None

# API error handling with retry logic  
try:
    response = model_instance.generate_content(prompt)
except Exception as e:
    cprint(f"Gemini API interaction failed: {e}", "red")
    return None
```

---

*This API documentation provides complete function references with code locations for efficient development and integration.*