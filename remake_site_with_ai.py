import os
import sys
from termcolor import cprint
from google import genai

# --- Gemini API helpers ---
def load_gemini_api_key():
    env_path = ".env.local"
    if not os.path.exists(env_path):
        cprint("[ERROR] .env.local not found!", "red")
        return None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GOOGLE_GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]
    cprint("[ERROR] GOOGLE_GEMINI_API_KEY not found in .env.local!", "red")
    return None

def gemini_generate_content(prompt, model="gemini-2.5-flash-preview-05-20"):
    api_key = load_gemini_api_key()
    if not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model, contents=prompt
        )
        return response.text
    except Exception as e:
        cprint(f"[ERROR] Gemini API call failed: {e}", "red")
        return None

# --- Enhancement logic ---
def build_full_html_prompt(copy_text, css_text, html_text, images_text):
    prompt = f"""
You are a world-class web designer and copywriter.

Given the following:
- The original website copy:
{copy_text}

- The original CSS:
{css_text}

- The original HTML:
{html_text}

- The image URLs:
{images_text}

Rebuild this page as a modern, visually appealing, responsive HTML+CSS file.
Maintain the brand's theme, colors, and imagery.
Improve the copy for clarity and engagement.
Output only the complete HTML code (including improved CSS, using the original as a base).
Reference the provided images in the HTML as appropriate.
"""
    return prompt

def process_page(page_dir, out_page_dir):
    copy_path = os.path.join(page_dir, "copy.txt")
    css_path = os.path.join(page_dir, "css.txt")
    html_path = os.path.join(page_dir, "page.html")
    images_path = os.path.join(page_dir, "images.txt")
    if not os.path.exists(copy_path) or not os.path.exists(html_path):
        cprint(f"[WARN] Missing copy.txt or page.html in {page_dir}, skipping.", "magenta")
        return
    with open(copy_path, "r", encoding="utf-8") as f:
        copy_text = f.read()
    with open(css_path, "r", encoding="utf-8") as f:
        css_text = f.read() if os.path.exists(css_path) else ""
    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()
    with open(images_path, "r", encoding="utf-8") as f:
        images_text = f.read() if os.path.exists(images_path) else ""
    cprint(f"[INFO] Sending full page context to Gemini for {page_dir}...", "cyan")
    prompt = build_full_html_prompt(copy_text, css_text, html_text, images_text)
    improved_html = gemini_generate_content(prompt)
    os.makedirs(out_page_dir, exist_ok=True)
    with open(os.path.join(out_page_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(improved_html or html_text)
    # Copy over other files for reference
    for fname in ["url.txt", "images.txt", "copy.txt", "css.txt", "page.html"]:
        src = os.path.join(page_dir, fname)
        dst = os.path.join(out_page_dir, fname)
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8") as fsrc, open(dst, "w", encoding="utf-8") as fdst:
                fdst.write(fsrc.read())
    cprint(f"[SUCCESS] Enhanced HTML page saved to {os.path.join(out_page_dir, 'index.html')}", "green")

def main():
    if len(sys.argv) < 2:
        cprint("Usage: python remake_site_with_ai.py <site_folder>", "yellow")
        sys.exit(1)
    site_folder = sys.argv[1]
    if not os.path.isdir(site_folder):
        cprint(f"[ERROR] {site_folder} is not a directory!", "red")
        sys.exit(1)
    out_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"
    if os.path.exists(out_folder):
        cprint(f"[WARN] Output folder {out_folder} exists, will overwrite enhanced pages.", "magenta")
    os.makedirs(out_folder, exist_ok=True)
    for page in os.listdir(site_folder):
        page_dir = os.path.join(site_folder, page)
        out_page_dir = os.path.join(out_folder, page)
        if os.path.isdir(page_dir):
            process_page(page_dir, out_page_dir)
    cprint(f"[DONE] Enhanced site saved in {out_folder}", "cyan")

if __name__ == "__main__":
    main() 