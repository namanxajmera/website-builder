import sys
import os
import re
from urllib.parse import urljoin, urlparse, quote
from termcolor import cprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import argparse
import hashlib
import json
import datetime
import socket
import ipaddress
from typing import Optional, Tuple, List

# Default values, can be overridden by CLI args
DEFAULT_MAX_PAGES = 20
DEFAULT_CRAWL_DEPTH = 2

# File name constants (consistent with remake_site_with_ai.py)
COPY_FILENAME = "copy.txt"
CSS_FILENAME = "css.txt"
HTML_FILENAME = "page.html"
IMAGES_FILENAME = "images.txt"
URL_FILENAME = "url.txt"

def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks by checking if target IP is public"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            cprint(f"[ERROR] Invalid URL: no hostname found in {url}", "red")
            return False
            
        # Resolve hostname to IP
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            
            # Check if IP is in private/reserved ranges
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                cprint(f"[ERROR] SSRF risk detected: {url} resolves to private/reserved IP {ip_str}", "red")
                return False
                
            # Additional checks for common internal ranges
            if (ip_obj.is_link_local or 
                str(ip_obj).startswith('169.254.') or  # Link-local
                str(ip_obj).startswith('224.') or      # Multicast
                str(ip_obj) == '0.0.0.0'):            # Unspecified
                cprint(f"[ERROR] SSRF risk detected: {url} resolves to restricted IP {ip_str}", "red")
                return False
                
            cprint(f"[INFO] URL safety check passed: {hostname} -> {ip_str}", "green")
            return True
            
        except socket.gaierror as e:
            cprint(f"[ERROR] DNS resolution failed for {hostname}: {e}", "red")
            return False
            
    except Exception as e:
        cprint(f"[ERROR] URL safety validation failed for {url}: {e}", "red")
        return False

def setup_driver():
    cprint("[INFO] Setting up Chrome WebDriver...", "cyan")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')  # Added for stability
        driver = webdriver.Chrome(options=chrome_options)
        # Set timeouts to prevent hanging
        driver.set_page_load_timeout(30)  # 30 seconds timeout for page loading
        driver.implicitly_wait(10)  # 10 seconds for element finding
        cprint("[SUCCESS] Chrome WebDriver initialized successfully with 30s page load timeout", "green")
        return driver
    except Exception as e:
        cprint(f"[ERROR] Failed to initialize Chrome WebDriver: {e}", "red")
        cprint("[INFO] Please ensure ChromeDriver is installed and in PATH", "yellow")
        sys.exit(1)

def is_internal_link(href, base_netloc):
    if not href or href.startswith("mailto:") or href.startswith("tel:"):
        return False
    parsed = urlparse(href)
    # Schemes like 'javascript:' should be ignored
    if parsed.scheme and parsed.scheme not in ['http', 'https']:
        return False
    if parsed.netloc and parsed.netloc != base_netloc:
        return False
    # We will handle fragment checks specifically in the crawl loop to avoid redundant crawls
    return True

def get_page_content(driver, url: str) -> Optional[Tuple[str, str, List[str], List[str]]]:
    cprint(f"[INFO] Loading page content from: {url}", "cyan")
    
    # SSRF protection: validate URL safety before making request
    if not is_safe_url(url):
        cprint(f"[ERROR] URL blocked for security reasons: {url}", "red")
        return None, None, None, None
    
    try:
        driver.get(url)
        cprint(f"[SUCCESS] Page loaded successfully", "green")
    except TimeoutException:
        cprint(f"[ERROR] Page load timeout for {url} (exceeded 30 seconds)", "red")
        return None, None, None, None
    except Exception as e:
        cprint(f"[ERROR] Failed to load page {url}: {e}", "red")
        return None, None, None, None
    
    try:
        
        cprint("[INFO] Parsing HTML content...", "cyan")
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        cprint("[INFO] Extracting images...", "cyan")
        images = set()
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Resolve relative URLs and add to set
                images.add(urljoin(url, src.strip()))
        cprint(f"[SUCCESS] Found {len(images)} images", "green")
        
        cprint("[INFO] Extracting CSS files...", "cyan")
        css_files = set()
        for link_tag in soup.find_all('link', rel='stylesheet'):
            href = link_tag.get('href')
            if href:
                css_files.add(urljoin(url, href.strip()))
        cprint(f"[SUCCESS] Found {len(css_files)} CSS files", "green")
        
        cprint("[INFO] Extracting inline styles...", "cyan")
        inline_styles = []
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                inline_styles.append(style_tag.string.strip())
        cprint(f"[SUCCESS] Found {len(inline_styles)} inline style blocks", "green")
        
        cprint("[INFO] Extracting text content...", "cyan")
        for script_or_style in soup(["script", "style"]): # Remove script and style tags before extracting text
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        text_length = len(text.split())
        cprint(f"[SUCCESS] Extracted {text_length} words of text content", "green")
        
        return html, images, text, css_files, inline_styles
    except Exception as e:
        cprint(f"[ERROR] Failed to load or parse {url}: {e}", "red")
        return None, set(), "", set(), []

def get_site_output_dir(domain):
    cprint(f"[INFO] Creating output directory for domain: {domain}", "cyan")
    base_dir = domain.replace(':', '_').replace('.', '_') # Sanitize for port numbers and dots
    output_dir = base_dir
    count = 1
    # Ensure a unique directory name
    while os.path.exists(output_dir):
        output_dir = f"{base_dir}_{count}"
        count += 1
    
    try:
        os.makedirs(output_dir)
        cprint(f"[SUCCESS] Created output directory: {output_dir}", "green")
        return output_dir
    except Exception as e:
        cprint(f"[ERROR] Failed to create output directory {output_dir}: {e}", "red")
        sys.exit(1)

def url_to_folder_name(url_str, base_url_str):
    cprint(f"[INFO] Converting URL to folder name: {url_str}", "cyan")
    parsed_url = urlparse(url_str)
    
    # Normalize by removing fragment and trailing slash for comparison and path generation
    normalized_url_path = parsed_url.path.rstrip('/')
    normalized_base_url_path = urlparse(base_url_str).path.rstrip('/')

    if normalized_url_path == normalized_base_url_path or normalized_url_path == "":
        folder_name = "home"
    else:
        path_segments = [seg for seg in normalized_url_path.split('/') if seg]
        if not path_segments: # Should be caught by home, but as a fallback
            folder_name = "root_page"
        else:
            # Take the last significant part of the path, or join them
            folder_name = path_segments[-1] 
            # If it ends with a common extension, remove it
            common_extensions = ['.html', '.htm', '.php', '.asp', '.aspx']
            for ext in common_extensions:
                if folder_name.endswith(ext):
                    folder_name = folder_name[:-len(ext)]
                    break
        
        # Sanitize folder name
        folder_name = re.sub(r'[^\w\-_]', '_', folder_name) # Allow word chars, hyphen, underscore
        folder_name = re.sub(r'_+', '_', folder_name)      # Collapse multiple underscores
        folder_name = folder_name.strip('_')               # Remove leading/trailing underscores
        
        if not folder_name: # If sanitization results in empty, default
            folder_name = "page_" + hashlib.md5(url_str.encode()).hexdigest()[:8]

    # Handle query parameters by appending a sanitized hash if they exist
    if parsed_url.query:
        query_hash = hashlib.md5(parsed_url.query.encode()).hexdigest()[:6]
        folder_name = f"{folder_name}_q{query_hash}"

    cprint(f"[SUCCESS] Generated folder name: {folder_name}", "green")
    return folder_name

def save_page_data(site_dir, folder_name, url, html, text, images, css_files, inline_styles):
    cprint(f"[INFO] Saving page data to folder: {folder_name}", "cyan")
    
    page_dir = os.path.join(site_dir, folder_name)
    try:
        os.makedirs(page_dir, exist_ok=True)
    except Exception as e:
        cprint(f"[ERROR] Failed to create page directory {page_dir}: {e}", "red")
        return False

    try:
        # Save URL
        with open(os.path.join(page_dir, URL_FILENAME), "w", encoding="utf-8") as f:
            f.write(url)
        cprint(f"  ✓ Saved {URL_FILENAME}", "green")

        # Save HTML
        with open(os.path.join(page_dir, HTML_FILENAME), "w", encoding="utf-8") as f:
            f.write(html)
        cprint(f"  ✓ Saved {HTML_FILENAME}", "green")

        # Save text content
        with open(os.path.join(page_dir, COPY_FILENAME), "w", encoding="utf-8") as f:
            f.write(text)
        cprint(f"  ✓ Saved {COPY_FILENAME}", "green")

        # Save images
        with open(os.path.join(page_dir, IMAGES_FILENAME), "w", encoding="utf-8") as f:
            for img_url in images:
                f.write(img_url + "\n")
        cprint(f"  ✓ Saved {IMAGES_FILENAME} with {len(images)} image URLs", "green")

        # Save CSS (external + inline)
        css_output_content = ""
        if css_files:
            css_output_content += "/* --- External CSS Files --- */\n"
            for css_url in css_files:
                css_output_content += f"/* Original URL: {css_url} */\n\n"
        if inline_styles:
            css_output_content += "\n/* --- Inline Styles --- */\n"
            for style_block in inline_styles:
                 css_output_content += f"<style>\n{style_block}\n</style>\n\n"
            
        with open(os.path.join(page_dir, CSS_FILENAME), "w", encoding="utf-8") as f:
            f.write(css_output_content)
        cprint(f"  ✓ Saved {CSS_FILENAME} ({len(css_files)} external CSS refs, {len(inline_styles)} inline styles)", "green")

        return True
    except Exception as e:
        cprint(f"[ERROR] Failed to save page data files in {page_dir}: {e}", "red")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl a website and extract content for AI processing.")
    parser.add_argument("url", help="The website URL to crawl")
    parser.add_argument("--max_pages", type=int, default=DEFAULT_MAX_PAGES,
                        help=f"Maximum number of pages to crawl (default: {DEFAULT_MAX_PAGES})")
    parser.add_argument("--depth", type=int, default=DEFAULT_CRAWL_DEPTH,
                        help=f"Maximum crawl depth (default: {DEFAULT_CRAWL_DEPTH})")
    
    args = parser.parse_args()

    target_url_raw = args.url
    # Normalize the initial target URL (remove fragment, trailing slash)
    parsed_target_url_raw = urlparse(target_url_raw)
    target_url = parsed_target_url_raw._replace(fragment="", query="").geturl().rstrip('/')
    if not target_url: # If only a fragment was passed
        target_url = parsed_target_url_raw._replace(path="/", fragment="", query="").geturl().rstrip('/')

    max_pages = args.max_pages
    crawl_depth = args.depth

    cprint("="*60, "cyan")
    cprint(f"🕷️  WEBSITE CRAWLER STARTING", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")
    cprint(f"[INFO] Target URL (normalized): {target_url}", "cyan")
    cprint(f"[INFO] Max pages: {max_pages}", "cyan")
    cprint(f"[INFO] Crawl depth: {crawl_depth}", "cyan")
    cprint("="*60, "cyan")

    try:
        parsed_url_obj = urlparse(target_url)
        if not parsed_url_obj.scheme or not parsed_url_obj.netloc:
            raise ValueError("Invalid URL format after normalization")
        base_netloc = parsed_url_obj.netloc
        cprint(f"[SUCCESS] Parsed base domain: {base_netloc}", "green")
    except Exception as e:
        cprint(f"[ERROR] Invalid URL '{target_url_raw}': {e}", "red")
        sys.exit(1)

    site_dir = get_site_output_dir(base_netloc)
    driver = setup_driver()

    try:
        visited_path_query = set() # Store URL path+query to avoid re-crawling same content due to fragments
        to_visit_queue = [(target_url, 1)]  # (url_with_fragment, depth)
        pages_crawled_count = 0
        
        # Keep track of unique URLs added to queue to avoid duplicates in queue
        queued_path_query_depth = set() 
        queued_path_query_depth.add((target_url, 1))

        cprint("\n" + "="*60, "cyan")
        cprint("🚀 STARTING CRAWL PROCESS", "cyan", attrs=["bold"])
        cprint("="*60, "cyan")

        while to_visit_queue and pages_crawled_count < max_pages:
            current_url_full, current_depth = to_visit_queue.pop(0)
            
            parsed_current_full = urlparse(current_url_full)
            # Key for uniqueness: URL without fragment
            url_path_query_key = parsed_current_full._replace(fragment="").geturl()

            if url_path_query_key in visited_path_query:
                cprint(f"[SKIP] Content for {url_path_query_key} (from {current_url_full}) already processed.", "yellow")
                continue
            
            if current_depth > crawl_depth:
                cprint(f"[SKIP] {current_url_full} - Max depth ({crawl_depth}) reached.", "yellow")
                continue

            cprint(f"\n[INFO] Crawling (depth {current_depth}, page {pages_crawled_count + 1}/{max_pages}): {current_url_full}", "cyan", attrs=["bold"])

            html, images, text, css_files, inline_styles = get_page_content(driver, url_path_query_key) # Crawl URL without fragment
            
            if html:
                visited_path_query.add(url_path_query_key)
                pages_crawled_count += 1
                
                folder_name_for_this_instance = url_to_folder_name(current_url_full, target_url)
                
                if save_page_data(site_dir, folder_name_for_this_instance, current_url_full, html, text, images, css_files, inline_styles):
                    cprint(f"[SUCCESS] Saved data for {current_url_full} (content from {url_path_query_key}) in {site_dir}/{folder_name_for_this_instance}", "green", attrs=["bold"])
                else:
                    cprint(f"[ERROR] Failed to save data for {current_url_full}", "red")

                if current_depth < crawl_depth:
                    cprint(f"[INFO] Searching for internal links on {url_path_query_key} (depth: {current_depth}/{crawl_depth})", "cyan")
                    soup = BeautifulSoup(html, "html.parser")
                    new_links_added_to_queue = 0
                    for link_tag in soup.find_all('a', href=True):
                        href_attr = link_tag['href']
                        absolute_link = urljoin(url_path_query_key, href_attr)
                        parsed_absolute_link = urlparse(absolute_link)
                        
                        # Key for queue uniqueness check (URL without fragment)
                        link_path_query_key_for_queue = parsed_absolute_link._replace(fragment="").geturl()

                        if is_internal_link(absolute_link, base_netloc) and \
                           link_path_query_key_for_queue not in visited_path_query and \
                           (link_path_query_key_for_queue, current_depth + 1) not in queued_path_query_depth:
                            
                            to_visit_queue.append((absolute_link, current_depth + 1))
                            queued_path_query_depth.add((link_path_query_key_for_queue, current_depth + 1))
                            new_links_added_to_queue += 1
                    
                    if new_links_added_to_queue > 0:
                        cprint(f"[SUCCESS] Added {new_links_added_to_queue} new unique internal links to queue", "green")
                    else:
                        cprint("[INFO] No new unique internal links found to add to queue", "yellow")
            else:
                cprint(f"[ERROR] Failed to get content for {url_path_query_key} (from {current_url_full})", "red")

        cprint("\n" + "="*60, "green")
        cprint("✅ CRAWL COMPLETED SUCCESSFULLY", "green", attrs=["bold"])
        cprint("="*60, "green")
        cprint(f"[DONE] Processed {pages_crawled_count} unique pages. Data saved in '{site_dir}'", "green", attrs=["bold"])
        cprint("="*60, "green")
        
        # Generate manifest file for reliable inter-script communication
        manifest_data = {
            "version": "1.0",
            "timestamp": datetime.datetime.now().isoformat(),
            "crawl_info": {
                "target_url": target_url,
                "base_netloc": base_netloc,
                "max_pages": max_pages,
                "crawl_depth": crawl_depth,
                "pages_crawled": pages_crawled_count
            },
            "output": {
                "site_dir": site_dir,
                "crawled_pages": list(visited_path_query)
            },
            "status": "completed"
        }
        
        manifest_path = os.path.join(site_dir, "crawl_manifest.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
            cprint(f"[SUCCESS] Manifest saved to {manifest_path}", "green")
        except Exception as e:
            cprint(f"[ERROR] Failed to save manifest: {e}", "red")
        
        print(site_dir) # For dashboard parsing (kept for backward compatibility)

    except KeyboardInterrupt:
        cprint("\n[WARN] Crawl interrupted by user", "yellow")
        cprint(f"[INFO] Partial data saved in '{site_dir}' ({pages_crawled_count} pages)", "cyan")
    except Exception as e:
        cprint(f"\n[ERROR] Unexpected error during crawling: {e}", "red")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'driver' in locals() and driver:
            cprint("[INFO] Closing WebDriver...", "cyan")
            driver.quit()
            cprint("[SUCCESS] WebDriver closed", "green")

if __name__ == "__main__":
    main() 