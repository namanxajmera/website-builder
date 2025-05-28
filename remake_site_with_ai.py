import os
import sys
from termcolor import cprint
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import argparse
import shutil
import json

# --- Gemini API helpers ---
def load_gemini_api_key():
    cprint("[INFO] Loading Gemini API key...", "cyan")
    # Attempt to load from environment variable first
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if api_key:
        cprint("[SUCCESS] API key loaded from environment variable", "green")
        return api_key
    
    # Fallback to .env.local
    env_path = ".env.local"
    cprint(f"[INFO] Checking for API key in {env_path}...", "cyan")
    if not os.path.exists(env_path):
        cprint("[ERROR] .env.local not found and GOOGLE_GEMINI_API_KEY env var not set!", "red")
        return None
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GOOGLE_GEMINI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    cprint("[SUCCESS] API key loaded from .env.local", "green")
                    return api_key
        cprint("[ERROR] GOOGLE_GEMINI_API_KEY not found in .env.local!", "red")
        return None
    except Exception as e:
        cprint(f"[ERROR] Failed to read .env.local: {e}", "red")
        return None

def gemini_generate_entire_site(all_pages_data_str, model_name="gemini-2.5-flash-preview-05-20"):
    cprint(f"[INFO] Initializing Gemini API for site generation...", "cyan")
    api_key = load_gemini_api_key()
    if not api_key:
        return None
    
    prompt = f"""
You are an expert web development agency tasked with a complete website overhaul.
You will receive data from an existing website, including HTML, CSS, text copy, and image URLs for multiple pages.

Your goal is to rebuild the entire website to be modern, visually appealing, **highly responsive (mobile-first)**, and **SEO-optimized**.

**Key Requirements:**

1.  **Consistency:** The new website must have a consistent design language, branding (colors, fonts, imagery based on original assets), navigation, header, and footer across all pages.
2.  **Component-Based Design (Conceptual):** While you will output full HTML for each page, internally, you should design and apply common components (e.g., header, footer, navigation menus, call-to-action buttons, cards) consistently.
3.  **Responsiveness:** All pages must be fully responsive and adapt gracefully to various screen sizes (desktop, tablet, mobile). Employ fluid layouts, flexible images, and media queries.
4.  **SEO Optimization:**
    *   Use semantic HTML5 tags (e.g., `<header>`, `<footer>`, `<nav>`, `<main>`, `<article>`, `<aside>`, `<section>`).
    *   Ensure proper heading hierarchy (H1, H2, H3, etc.).
    *   Generate descriptive meta tags (title, description) for each page, derived from its content. These should be included in the `<head>` of each page's HTML.
    *   Optimize images with appropriate `alt` text (you can generate generic descriptive alt text if not provided, e.g., "Image related to [page topic]").
    *   Ensure clean, well-structured HTML.
5.  **Content Modernization:** Improve the original copy for clarity, engagement, and conciseness while retaining the core message.
6.  **Asset Usage:** Utilize the provided image URLs from the original site. Reference them directly in the `<img>` tags.
7.  **Navigation & Linking:**
    *   **CRITICAL**: Ensure ALL navigation elements (header menus, footer links, buttons, CTAs) are properly linked to the appropriate pages.
    *   **Header Navigation**: Every page should have a consistent header with working navigation links to all other pages.
    *   **Footer Links**: Include working footer navigation that mirrors the main navigation.
    *   **Cross-Page References**: Any mentions of services, about sections, contact info, etc. should be properly linked to their respective pages.
    *   **Call-to-Action Buttons**: Ensure buttons like "Contact Us", "Learn More", "Get Started" link to the appropriate pages (usually contact or about pages).
    *   **Logo Links**: Make sure the site logo/brand name links back to the home page.
8.  **Output Format:**
    You MUST output a single JSON object. This JSON object should have two top-level keys:
    *   `"global_css"`: A string containing all the CSS rules required for the entire website. This will be saved as a single `global_styles.css` file.
    *   `"pages"`: An object where each key is the original page identifier (e.g., "home", "about_us", "contact_page") and the value is the complete HTML content for that page (as a string).
        *   Each HTML page should be a full document (starting with `<!DOCTYPE html>`).
        *   Each HTML page must link to the `global_styles.css` file correctly in its `<head>` section. Given that `global_styles.css` will be at the root of the AI output directory (e.g., `example.com_ai/global_styles.css`) and page HTML files will be in subdirectories (e.g., `example.com_ai/home/index.html`), the link should be `<link rel="stylesheet" href="../global_styles.css">`.
9.  **Internal Linking:**
    *   When linking between pages of the rebuilt site, use relative paths. For a page with identifier `target_page_id`, the link from another page (e.g., from `current_page_id/index.html`) should be `../target_page_id/index.html`. For example, a link from the 'home' page to the 'about' page should be `<a href="../about/index.html">About Us</a>`.
    *   **Navigation Examples**:
        - Home page link: `<a href="../home/index.html">Home</a>`
        - About page link: `<a href="../about/index.html">About</a>`
        - Contact page link: `<a href="../contact/index.html">Contact</a>`
        - Services page link: `<a href="../services/index.html">Services</a>`

**Input Data (Original Website Structure):**
The following XML-like structure contains the data for all crawled pages. Each `<page id="...">` attribute corresponds to the page identifier you should use as keys in the `"pages"` object of your JSON output.
<website_data>
{all_pages_data_str}
</website_data>

---
**IMPORTANT**: Respond ONLY with the JSON object as specified. Do not include any other text, explanations, or markdown formatting around the JSON.
The HTML content within the JSON should be pure HTML.
---
"""
    
    data_size_kb = len(all_pages_data_str) / 1024
    cprint(f"[INFO] Preparing to send {data_size_kb:.1f}KB of site data to Gemini", "cyan")
    cprint(f"[INFO] Using model: {model_name}", "cyan")
    cprint(f"[INFO] This may take several minutes for large sites...", "yellow")
    
    response_text = None
    try:
        cprint("[INFO] Configuring Gemini API...", "cyan")
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(
            model_name=model_name,
            # safety_settings allow all content - use with caution and ensure your use case complies with policies
            # safety_settings={
            #     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            # }
        )
        cprint("[SUCCESS] Gemini API configured successfully", "green")
        
        cprint("[INFO] Sending request to Gemini AI... ⏳", "cyan", attrs=["bold"])
        response = model_instance.generate_content(
            contents=prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5, 
                # max_output_tokens=8192, # Explicitly set if needed, flash default is 8192. Pro might be higher.
            )
        )
        cprint("[SUCCESS] Received response from Gemini AI! 🎉", "green", attrs=["bold"])
        
        cprint("[INFO] Processing AI response...", "cyan")

        # Try to access text, handle potential errors
        try:
            if response.parts:
                response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else: # Fallback if .parts is empty but .text might work (older API behavior or specific cases)
                response_text = response.text 
        except Exception as e:
            cprint(f"[WARN] Could not access response.text or response.parts directly: {e}", "yellow")
            cprint(f"[DEBUG] Full response object: {response}", "yellow")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                cprint(f"[ERROR] Prompt blocked due to: {response.prompt_feedback.block_reason}", "red")
                cprint(f"[DEBUG] Safety ratings: {response.prompt_feedback.safety_ratings}", "yellow")
            if response.candidates and response.candidates[0].finish_reason:
                 cprint(f"[ERROR] Generation candidate finished due to: {response.candidates[0].finish_reason}", "red")
                 if response.candidates[0].finish_reason.name == "MAX_TOKENS":
                     cprint("[HINT] The model may have run out of output tokens. Consider a model with larger output capacity or reducing prompt/output complexity.", "yellow")
                 elif response.candidates[0].finish_reason.name == "SAFETY":
                     cprint("[HINT] Content generation stopped due to safety settings. Review safety ratings above.", "yellow")
            return None # Critical error if we can't get text

        if not response_text:
            cprint("[ERROR] Gemini response was empty or contained no text parts.", "red")
            cprint(f"[DEBUG] Full response object: {response}", "yellow")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                cprint(f"[ERROR] Prompt blocked due to: {response.prompt_feedback.block_reason}", "red")
            if response.candidates and response.candidates[0].finish_reason:
                 cprint(f"[ERROR] Generation candidate finished due to: {response.candidates[0].finish_reason}", "red")
            return None

        cleaned_text = response_text.strip()
        
        # Clean markdown formatting if present
        if cleaned_text.startswith("```json"):
            cprint("[INFO] Removing ```json markdown wrapper", "cyan")
            cleaned_text = cleaned_text[len("```json"):] 
        elif cleaned_text.startswith("```"): 
            cprint("[INFO] Removing ``` markdown wrapper", "cyan")
            cleaned_text = cleaned_text[len("```"):]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")]
        
        cprint("[INFO] Parsing JSON response...", "cyan")
        ai_json_response = json.loads(cleaned_text)
        
        # Validate response structure
        if not isinstance(ai_json_response, dict):
            raise ValueError("Response is not a JSON object")
        if "global_css" not in ai_json_response:
            raise ValueError("Missing 'global_css' key in response")
        if "pages" not in ai_json_response:
            raise ValueError("Missing 'pages' key in response")
        if not isinstance(ai_json_response["pages"], dict):
            raise ValueError("'pages' value is not an object")
            
        pages_count = len(ai_json_response["pages"])
        css_size_kb = len(ai_json_response["global_css"]) / 1024
        cprint(f"[SUCCESS] Parsed AI response: {pages_count} pages, {css_size_kb:.1f}KB CSS", "green")
        
        return ai_json_response
        
    except json.JSONDecodeError as e:
        cprint(f"[ERROR] Failed to parse JSON response from Gemini: {e}", "red")
        cprint(f"[DEBUG] Raw text before JSON parse (first 500 chars):", "yellow")
        if response_text:
            cprint(f">>>>\n{response_text[:500]}\n<<<<", "yellow")
        else:
            cprint("[DEBUG] No text was extracted from the response to parse.", "yellow")
        return None
    except Exception as e:
        cprint(f"[ERROR] Gemini API interaction or processing failed: {e}", "red")
        import traceback
        traceback.print_exc()
        # More detailed debugging for the response object if available
        if 'response' in locals():
            cprint(f"[DEBUG] Full response object at time of error: {response}", "yellow")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
               cprint(f"[ERROR] Prompt blocked due to: {response.prompt_feedback.block_reason}", "red")
            if response.candidates:
                for i, cand in enumerate(response.candidates):
                    cprint(f"[DEBUG] Candidate {i} Finish Reason: {cand.finish_reason}", "yellow")
                    cprint(f"[DEBUG] Candidate {i} Safety Ratings: {cand.safety_ratings}", "yellow")
        return None

def main():
    parser = argparse.ArgumentParser(description="Rebuild an entire crawled website using AI with a holistic approach.")
    parser.add_argument("site_folder", help="The folder containing the crawled site data (e.g., example.com).")
    parser.add_argument("--model", default="gemini-2.5-flash-preview-05-20",
                        help="Name of the Gemini model to use (e.g., gemini-2.5-flash-preview-05-20, gemini-1.5-pro-latest).")
    
    args = parser.parse_args()

    site_folder = args.site_folder
    
    cprint("="*70, "cyan")
    cprint("🤖 AI WEBSITE REBUILDER STARTING", "cyan", attrs=["bold"])
    cprint("="*70, "cyan")
    cprint(f"[INFO] Source folder: {site_folder}", "cyan")
    cprint(f"[INFO] AI Model: {args.model}", "cyan")
    cprint("="*70, "cyan")

    # Validate input folder
    if not os.path.isdir(site_folder):
        cprint(f"[ERROR] {site_folder} is not a directory!", "red")
        sys.exit(1)

    # Set up output folder
    out_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"
    cprint(f"[INFO] Output folder will be: {out_folder}", "cyan")
    
    if os.path.exists(out_folder):
        cprint(f"[WARN] Output folder {out_folder} already exists, will overwrite files", "magenta")
    
    try:
        os.makedirs(out_folder, exist_ok=True)
        cprint(f"[SUCCESS] Output directory ready: {out_folder}", "green")
    except Exception as e:
        cprint(f"[ERROR] Failed to create output directory: {e}", "red")
        sys.exit(1)

    # Scan for page subdirectories
    cprint(f"[INFO] Scanning for page data in {site_folder}...", "cyan")
    try:
        page_subdirs = [f.name for f in os.scandir(site_folder) if f.is_dir()]
        cprint(f"[SUCCESS] Found {len(page_subdirs)} page directories: {', '.join(page_subdirs) if page_subdirs else 'None'}", "green")
    except Exception as e:
        cprint(f"[ERROR] Failed to scan site folder: {e}", "red")
        sys.exit(1)

    if not page_subdirs:
        cprint(f"[ERROR] No page subdirectories found in {site_folder}. Ensure crawl_site.py ran successfully.", "red")
        sys.exit(1)

    # Load page data
    all_pages_data = []
    successful_pages_loaded = 0
    
    cprint("\n" + "="*50, "cyan")
    cprint("📄 LOADING PAGE DATA", "cyan", attrs=["bold"])
    cprint("="*50, "cyan")

    for page_subdir_name in page_subdirs:
        page_dir = os.path.join(site_folder, page_subdir_name)
        cprint(f"[INFO] Processing page data from directory: {page_subdir_name}", "cyan")
        
        # Define expected files
        copy_path = os.path.join(page_dir, "copy.txt")
        css_path = os.path.join(page_dir, "css.txt")
        html_path = os.path.join(page_dir, "page.html")
        images_path = os.path.join(page_dir, "images.txt")
        url_path = os.path.join(page_dir, "url.txt")

        # Check for essential files
        essential_files = [copy_path, html_path, url_path]
        missing_files = [f for f in essential_files if not os.path.exists(f)]
        
        if missing_files:
            cprint(f"  [WARN] Skipping {page_subdir_name} - missing essential files: {[os.path.basename(f) for f in missing_files]}", "magenta")
            continue

        try:
            # Load all page data
            with open(url_path, "r", encoding="utf-8") as f: 
                page_url = f.read().strip()
                cprint(f"    ✓ Loaded URL: {page_url}", "green")
                
            with open(html_path, "r", encoding="utf-8") as f: 
                original_html = f.read()
                html_size_kb = len(original_html) / 1024
                cprint(f"    ✓ Loaded HTML: {html_size_kb:.1f}KB", "green")
                
            with open(copy_path, "r", encoding="utf-8") as f: 
                original_copy = f.read()
                word_count = len(original_copy.split())
                cprint(f"    ✓ Loaded copy: {word_count} words", "green")
            
            # Load optional files
            original_css = "/* No external CSS file found or it was empty. */"
            if os.path.exists(css_path):
                with open(css_path, "r", encoding="utf-8") as f: 
                    css_content = f.read().strip()
                    if css_content:
                        original_css = css_content
                        cprint(f"    ✓ Loaded CSS: {len(css_content)} chars", "green")
                    else:
                        cprint(f"    ⚠ CSS file empty for {page_subdir_name}", "yellow")
            else:
                cprint(f"    ⚠ No CSS file (css.txt) found for {page_subdir_name}", "yellow")
            
            image_urls = "<!-- No image URLs provided or images.txt was empty. -->"
            if os.path.exists(images_path):
                with open(images_path, "r", encoding="utf-8") as f: 
                    content = f.read().strip()
                    if content:
                        image_urls = content
                        image_count = len(content.split('\n'))
                        cprint(f"    ✓ Loaded images: {image_count} URLs", "green")
                    else:
                        cprint(f"    ⚠ Images file empty for {page_subdir_name}", "yellow")
            else:
                cprint(f"    ⚠ No images file (images.txt) found for {page_subdir_name}", "yellow")

            # Create XML data block
            page_data_xml = f"""  <page id="{page_subdir_name}">
    <url><![CDATA[{page_url}]]></url>
    <original_html><![CDATA[{original_html}]]></original_html>
    <original_css><![CDATA[{original_css}]]></original_css>
    <original_copy><![CDATA[{original_copy}]]></original_copy>
    <image_urls><![CDATA[{image_urls}]]></image_urls>
  </page>"""
            all_pages_data.append(page_data_xml)
            successful_pages_loaded += 1
            cprint(f"  [SUCCESS] Successfully processed data for page: {page_subdir_name}", "green", attrs=["bold"])
            
        except Exception as e:
            cprint(f"  [ERROR] Failed to load data for {page_subdir_name}: {e}", "red")

    if not all_pages_data:
        cprint(f"\n[ERROR] No valid page data could be loaded after processing all subdirectories. AI processing cannot continue.", "red")
        sys.exit(1)
    
    cprint(f"\n[SUCCESS] Successfully loaded data for {successful_pages_loaded} pages for AI processing", "green", attrs=["bold"])
    
    # Prepare data for AI
    all_pages_data_str = "\n".join(all_pages_data)
    
    cprint("\n" + "="*50, "cyan")
    cprint("🤖 AI PROCESSING", "cyan", attrs=["bold"])
    cprint("="*50, "cyan")
    
    # Send to AI
    ai_response = gemini_generate_entire_site(all_pages_data_str, model_name=args.model)

    if not ai_response:
        cprint("\n[ERROR] AI processing failed - no valid response received from Gemini.", "red")
        sys.exit(1)

    # Validate AI response structure (already did in gemini_generate_entire_site, but good for safety)
    if not ("global_css" in ai_response and "pages" in ai_response and isinstance(ai_response["pages"], dict)):
        cprint(f"\n[ERROR] Invalid AI response structure after receiving from Gemini.", "red")
        cprint(f"[DEBUG] Response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}", "yellow")
        sys.exit(1)

    cprint("\n" + "="*50, "green")
    cprint("💾 SAVING AI-GENERATED WEBSITE", "green", attrs=["bold"])
    cprint("="*50, "green")

    # Save global CSS
    cprint("[INFO] Saving global stylesheet...", "cyan")
    try:
        global_css_path = os.path.join(out_folder, "global_styles.css")
        with open(global_css_path, "w", encoding="utf-8") as f:
            f.write(ai_response["global_css"])
        css_size_kb = len(ai_response["global_css"]) / 1024
        cprint(f"  [SUCCESS] Saved global CSS: {global_css_path} ({css_size_kb:.1f}KB)", "green", attrs=["bold"])
    except Exception as e:
        cprint(f"  [ERROR] Failed to save global CSS: {e}", "red")
        sys.exit(1) # Critical failure if CSS can't be saved

    # Save individual pages
    saved_page_count = 0
    failed_page_save_count = 0
    
    for page_id, page_html in ai_response["pages"].items():
        cprint(f"[INFO] Saving AI-generated content for page: {page_id}", "cyan")
        
        if not isinstance(page_html, str):
            cprint(f"  [WARN] HTML content for page '{page_id}' is not a string (type: {type(page_html)}), skipping save.", "magenta")
            failed_page_save_count += 1
            continue

        try:
            # Create page directory
            page_out_dir = os.path.join(out_folder, page_id)
            os.makedirs(page_out_dir, exist_ok=True)
            
            # Save main HTML file
            output_html_path = os.path.join(page_out_dir, "index.html")
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(page_html)
            
            html_size_kb = len(page_html) / 1024
            cprint(f"    ✓ Saved index.html ({html_size_kb:.1f}KB)", "green")
            
            # Copy original reference files
            original_page_dir = os.path.join(site_folder, page_id)
            if os.path.isdir(original_page_dir):
                reference_files_copied_count = 0
                for fname in ["url.txt", "images.txt", "copy.txt", "css.txt", "page.html"]:
                    src = os.path.join(original_page_dir, fname)
                    dst = os.path.join(page_out_dir, f"original_{fname}")
                    if os.path.exists(src):
                        try:
                            shutil.copy2(src, dst)
                            reference_files_copied_count += 1
                        except Exception as e_copy:
                            cprint(f"    ⚠ Could not copy reference file {fname} for {page_id}: {e_copy}", "yellow")
                
                if reference_files_copied_count > 0:
                    cprint(f"    ✓ Copied {reference_files_copied_count} original reference files for {page_id}", "green")
            else:
                cprint(f"    [WARN] Original page directory not found for reference files: {original_page_dir}", "magenta")

            saved_page_count += 1
            cprint(f"  [SUCCESS] Successfully completed saving for page: {page_id}", "green", attrs=["bold"])
            
        except Exception as e_save:
            cprint(f"  [ERROR] Failed to save files for page {page_id}: {e_save}", "red")
            failed_page_save_count += 1

    # Final summary
    cprint("\n" + "="*70, "green")
    cprint("🎉 AI WEBSITE REBUILD COMPLETED", "green", attrs=["bold"])
    cprint("="*70, "green")
    
    if saved_page_count > 0:
        cprint(f"[SUCCESS] {saved_page_count} pages were successfully generated and saved.", "green", attrs=["bold"])
        cprint(f"[SUCCESS] Output directory: {out_folder}", "green", attrs=["bold"])
        
        if failed_page_save_count > 0:
            cprint(f"[WARN] {failed_page_save_count} pages encountered issues during saving.", "yellow")
        
        cprint("\n📁 Generated files include:", "cyan")
        cprint(f"  • global_styles.css (Global stylesheet for the new site)", "cyan")
        # List only successfully saved pages from AI response
        successfully_saved_page_ids = [pid for pid, html in ai_response["pages"].items() if isinstance(html, str)][:5] # Show first 5
        for page_id in successfully_saved_page_ids:
            cprint(f"  • {page_id}/index.html (Modernized page content)", "cyan")
        if len(ai_response["pages"]) > 5:
            cprint(f"  • ... and {len(ai_response['pages']) - 5} more page(s).", "cyan")
        
        cprint(f"\n🌐 Your modernized website is ready! To preview, open any index.html file from the '{out_folder}' directory in your browser.", "green", attrs=["bold"])
        
    else:
        cprint(f"[ERROR] No pages were successfully saved from the AI response, although the AI call may have succeeded.", "red")
        if failed_page_save_count > 0:
            cprint(f"[INFO] {failed_page_save_count} pages encountered issues during the saving process.", "yellow")
        sys.exit(1) # Indicate failure if no pages saved

    cprint("="*70, "green")

if __name__ == "__main__":
    main() 