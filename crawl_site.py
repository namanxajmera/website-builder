import sys
import os
import re
from urllib.parse import urljoin, urlparse, quote
from termcolor import cprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

MAX_PAGES = 20
CRAWL_DEPTH = 2

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options)

def is_internal_link(href, base_netloc):
    if not href or href.startswith("mailto:") or href.startswith("tel:"):
        return False
    parsed = urlparse(href)
    if parsed.netloc and parsed.netloc != base_netloc:
        return False
    if href.startswith("#"):
        return False
    return True

def get_page_content(driver, url):
    try:
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        # Extract all image URLs (absolute)
        images = set()
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.add(urljoin(url, src))
        # Extract all CSS file URLs (absolute)
        css_files = set()
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                css_files.add(urljoin(url, href))
        # Extract inline <style> blocks
        inline_styles = []
        for style in soup.find_all('style'):
            if style.string:
                inline_styles.append(style.string)
        # Extract visible text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return html, images, text, css_files, inline_styles
    except Exception as e:
        cprint(f"[ERROR] Failed to load {url}: {e}", "red")
        return None, set(), "", set(), []

def get_site_output_dir(domain):
    base_dir = domain.replace(':', '_')
    output_dir = base_dir
    count = 1
    while os.path.exists(output_dir):
        output_dir = f"{base_dir}_{count}"
        count += 1
    os.makedirs(output_dir)
    return output_dir

def url_to_folder_name(url, base_url):
    parsed = urlparse(url)
    if url.rstrip('/') == base_url.rstrip('/'):
        return "home"
    path = parsed.path.strip('/')
    if not path:
        path = "root"
    if parsed.query:
        path += "_" + quote(parsed.query, safe='')
    safe_path = path.replace('/', '_')
    return safe_path

def save_page_data(site_dir, folder_name, url, html, images, text, css_files, inline_styles):
    page_dir = os.path.join(site_dir, folder_name)
    os.makedirs(page_dir, exist_ok=True)
    try:
        with open(os.path.join(page_dir, "url.txt"), "w", encoding="utf-8") as f:
            f.write(url)
        with open(os.path.join(page_dir, "page.html"), "w", encoding="utf-8") as f:
            f.write(html)
        with open(os.path.join(page_dir, "images.txt"), "w", encoding="utf-8") as f:
            for img in images:
                f.write(img + "\n")
        with open(os.path.join(page_dir, "copy.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        with open(os.path.join(page_dir, "css.txt"), "w", encoding="utf-8") as f:
            for css in css_files:
                f.write(css + "\n")
            if inline_styles:
                f.write("\n\n/* Inline Styles */\n")
                for style in inline_styles:
                    f.write(style + "\n")
        cprint(f"[SUCCESS] Saved data for {url} in {page_dir}", "green")
    except Exception as e:
        cprint(f"[ERROR] Failed to save data for {url}: {e}", "red")

def crawl_site(start_url):
    cprint(f"[INFO] Starting crawl at {start_url}", "cyan")
    parsed_start = urlparse(start_url)
    base_netloc = parsed_start.netloc
    base_url = start_url
    site_dir = get_site_output_dir(base_netloc)
    visited = set()
    to_visit = [(start_url, 1)]  # (url, depth)
    driver = setup_driver()
    try:
        while to_visit and len(visited) < MAX_PAGES:
            url, depth = to_visit.pop(0)
            if url in visited or depth > CRAWL_DEPTH:
                continue
            cprint(f"[INFO] Crawling (depth {depth}): {url}", "yellow")
            html, images, text, css_files, inline_styles = get_page_content(driver, url)
            if html:
                folder_name = url_to_folder_name(url, base_url)
                save_page_data(site_dir, folder_name, url, html, images, text, css_files, inline_styles)
                visited.add(url)
                if depth < CRAWL_DEPTH:
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all('a', href=True):
                        link = urljoin(url, a['href'])
                        if is_internal_link(link, base_netloc) and link not in visited and link not in [u for u, _ in to_visit]:
                            to_visit.append((link, depth + 1))
            else:
                cprint(f"[WARN] Skipping {url} due to load error.", "magenta")
            if len(visited) >= MAX_PAGES:
                cprint(f"[INFO] Reached max page limit ({MAX_PAGES}). Stopping crawl.", "cyan")
                break
    finally:
        driver.quit()
    cprint(f"[DONE] Crawled {len(visited)} pages. Data in '{site_dir}'", "cyan")

def main():
    if len(sys.argv) < 2:
        cprint("Usage: python crawl_site.py <url>", "yellow")
        sys.exit(1)
    start_url = sys.argv[1]
    crawl_site(start_url)

if __name__ == "__main__":
    main() 