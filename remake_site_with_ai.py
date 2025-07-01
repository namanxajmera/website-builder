import os
import sys
from termcolor import cprint
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import argparse
import shutil
import json
import tempfile
from typing import Optional, Dict, Any

# --- File name constants ---
COPY_FILENAME = "copy.txt"
CSS_FILENAME = "css.txt"
HTML_FILENAME = "page.html"
IMAGES_FILENAME = "images.txt"
URL_FILENAME = "url.txt"

# --- Gemini API helpers ---
def load_gemini_api_key() -> Optional[str]:
    """Load Gemini API key from environment variable."""
    cprint("[INFO] Loading Gemini API key...", "cyan")
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if api_key:
        cprint("[SUCCESS] API key loaded from environment variable", "green")
        return api_key
    else:
        cprint("[ERROR] GOOGLE_GEMINI_API_KEY environment variable not set!", "red")
        cprint("[INFO] Please set your API key: export GOOGLE_GEMINI_API_KEY=your-api-key", "yellow")
        return None

def gemini_generate_entire_site(all_pages_data_str: str, model_name: str = "gemini-2.5-flash", temperature: float = 0.5) -> Optional[Dict[str, Any]]:
    cprint(f"[INFO] Initializing Gemini API for site generation...", "cyan")
    api_key = load_gemini_api_key()
    if not api_key:
        return None
    
    # Load prompt from external file
    prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "rebuild_prompt.txt")
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        prompt = prompt_template.format(all_pages_data_str=all_pages_data_str)
        cprint(f"[SUCCESS] Loaded prompt template from {prompt_file}", "green")
    except Exception as e:
        cprint(f"[ERROR] Failed to load prompt template: {e}", "red")
        return None
    
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
                temperature=temperature, 
                # max_output_tokens=8192, # Explicitly set if needed, flash default is 8192. Pro might be higher.
            )
        )
        cprint("[SUCCESS] Received response from Gemini AI! 🎉", "green", attrs=["bold"])
        
        cprint("[INFO] Processing AI response...", "cyan")

        # Try to access text, handle potential errors
        try:
            if response.parts:
                response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else: 
                response_text = response.text 
        except Exception as e:
            cprint(f"[WARN] Could not access response.text or response.parts directly: {e}", "yellow")
            cprint(f"[DEBUG] Full response object: {response}", "yellow")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                cprint(f"[ERROR] Prompt blocked due to: {response.prompt_feedback.block_reason}", "red")
                cprint(f"[DEBUG] Safety ratings: {response.prompt_feedback.safety_ratings}", "yellow")
            if response.candidates and response.candidates[0].finish_reason:
                 cprint(f"[ERROR] Generation candidate finished due to: {response.candidates[0].finish_reason}", "red")
                 if hasattr(response.candidates[0].finish_reason, 'name') and response.candidates[0].finish_reason.name == "MAX_TOKENS":
                     cprint("[HINT] The model may have run out of output tokens. Consider a model with larger output capacity or reducing prompt/output complexity.", "yellow")
                 elif hasattr(response.candidates[0].finish_reason, 'name') and response.candidates[0].finish_reason.name == "SAFETY":
                     cprint("[HINT] Content generation stopped due to safety settings. Review safety ratings above.", "yellow")
            return None

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
        if "site_structure_decision" not in ai_json_response:
            raise ValueError("Missing 'site_structure_decision' key in response")
        if "global_css" not in ai_json_response:
            raise ValueError("Missing 'global_css' key in response")
        if "html_files" not in ai_json_response:
            raise ValueError("Missing 'html_files' key in response")
        if not isinstance(ai_json_response["html_files"], dict):
            raise ValueError("'html_files' value is not an object")
            
        pages_count = len(ai_json_response["html_files"])
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

def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild an entire crawled website using AI with a holistic approach.")
    parser.add_argument("site_folder", help="The folder containing the crawled site data (e.g., example.com).")
    parser.add_argument("--model", default="gemini-2.5-flash",
                        help="Name of the Gemini model to use (e.g., gemini-2.5-flash, gemini-2.5-pro).")
    parser.add_argument("--temperature", type=float, default=0.5,
                        help="Temperature for AI generation (0.0-1.0, higher values make output more creative/random).")
    
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

    # Set up atomic output folder creation
    final_out_folder = site_folder.rstrip('/').rstrip('\\') + "_ai"
    temp_out_folder = site_folder.rstrip('/').rstrip('\\') + "_ai_temp"
    cprint(f"[INFO] Final output folder will be: {final_out_folder}", "cyan")
    
    # Clean up any existing temp directory
    if os.path.exists(temp_out_folder):
        cprint(f"[INFO] Cleaning up previous temporary directory: {temp_out_folder}", "yellow")
        try:
            shutil.rmtree(temp_out_folder)
        except Exception as e:
            cprint(f"[ERROR] Failed to clean up temp directory: {e}", "red")
            sys.exit(1)
    
    try:
        os.makedirs(temp_out_folder, exist_ok=False)  # Should not exist after cleanup
        cprint(f"[SUCCESS] Temporary output directory created: {temp_out_folder}", "green")
        out_folder = temp_out_folder  # Use temp folder during generation
    except Exception as e:
        cprint(f"[ERROR] Failed to create temporary output directory: {e}", "red")
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
        copy_path = os.path.join(page_dir, COPY_FILENAME)
        css_path = os.path.join(page_dir, CSS_FILENAME)
        html_path = os.path.join(page_dir, HTML_FILENAME)
        images_path = os.path.join(page_dir, IMAGES_FILENAME)
        url_path = os.path.join(page_dir, URL_FILENAME)

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
    ai_response = gemini_generate_entire_site(all_pages_data_str, model_name=args.model, temperature=args.temperature)

    if not ai_response:
        cprint("\n[ERROR] AI processing failed - no valid response received from Gemini.", "red")
        sys.exit(1)

    # Validate AI response structure (already did in gemini_generate_entire_site, but good for safety)
    if not ("site_structure_decision" in ai_response and "global_css" in ai_response and "html_files" in ai_response and isinstance(ai_response["html_files"], dict)):
        cprint(f"\n[ERROR] Invalid AI response structure after receiving from Gemini.", "red")
        cprint(f"[DEBUG] Response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}", "yellow")
        sys.exit(1)

    cprint("\n" + "="*50, "green")
    cprint("💾 SAVING AI-GENERATED WEBSITE", "green", attrs=["bold"])
    cprint("="*50, "green")

    # Display AI's structural decision
    if "site_structure_decision" in ai_response:
        cprint(f"[AI DECISION] {ai_response['site_structure_decision']}", "magenta", attrs=["bold"])
    
    # Save AI decision for dashboard display
    decision_path = os.path.join(out_folder, "ai_decision.txt")
    try:
        with open(decision_path, "w", encoding="utf-8") as f:
            f.write(ai_response['site_structure_decision'])
        cprint(f"[INFO] AI decision saved to {decision_path}", "cyan")
    except Exception as e:
        cprint(f"[WARN] Failed to save AI decision: {e}", "yellow")
    
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

    # Save HTML files directly in root output directory
    saved_page_count = 0
    failed_page_save_count = 0
    
    for filename, page_html_content in ai_response["html_files"].items():
        cprint(f"[INFO] Saving HTML file: {filename}", "cyan")
        
        # Enhanced security validation for filename
        if not filename.endswith(".html"):
            cprint(f"  [WARN] Skipping non-HTML filename from AI: {filename}", "magenta")
            failed_page_save_count += 1
            continue
        
        # Normalize and validate path to prevent directory traversal
        normalized_filename = os.path.normpath(filename)
        if (normalized_filename != filename or 
            ".." in normalized_filename or 
            "/" in normalized_filename or "\\" in normalized_filename or
            normalized_filename.startswith('.') or
            any(ord(c) < 32 for c in normalized_filename)):  # Check for control characters
            cprint(f"  [WARN] Skipping potentially unsafe filename from AI: {filename}", "magenta")
            failed_page_save_count += 1
            continue
            
        if not isinstance(page_html_content, str):
            cprint(f"  [WARN] HTML content for '{filename}' is not a string (type: {type(page_html_content)}), skipping.", "magenta")
            failed_page_save_count += 1
            continue

        # Validate HTML content with BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            parsed_html = BeautifulSoup(page_html_content, "html.parser")
            # Basic validation: check if parsing succeeded and content is reasonable
            if not parsed_html or len(str(parsed_html).strip()) < 50:
                cprint(f"  [WARN] AI-generated HTML for '{filename}' appears to be malformed or too short.", "magenta")
                cprint(f"        Content preview: {page_html_content[:100]}...", "yellow")
                # Continue with saving anyway, but log the warning
            else:
                cprint(f"  ✓ HTML validation passed for {filename}", "green")
        except Exception as e_validation:
            cprint(f"  [WARN] HTML validation failed for '{filename}': {e_validation}", "magenta")
            cprint(f"        Content preview: {page_html_content[:100]}...", "yellow")
            # Continue with saving anyway since validation failure doesn't mean unusable content

        try:
            # Save HTML file directly in root output directory
            output_html_path = os.path.join(out_folder, filename)
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(page_html_content)
            
            html_size_kb = len(page_html_content) / 1024
            cprint(f"    ✓ Saved {filename} ({html_size_kb:.1f}KB)", "green")
            saved_page_count += 1
            
        except Exception as e_save:
            cprint(f"  [ERROR] Failed to save {filename}: {e_save}", "red")
            failed_page_save_count += 1

    # Copy original crawled site data to a subfolder for reference
    cprint("[INFO] Preserving original crawled data for reference...", "cyan")
    try:
        originals_ref_dir = os.path.join(out_folder, "original_crawled_data")
        if os.path.exists(site_folder):
            shutil.copytree(site_folder, originals_ref_dir, dirs_exist_ok=True)
            cprint(f"  ✓ Original data preserved in: {originals_ref_dir}", "green")
        else:
            cprint(f"  [WARN] Source folder {site_folder} not found for reference copy", "yellow")
    except Exception as e_copy:
        cprint(f"  [WARN] Could not copy original crawled data: {e_copy}", "yellow")

    # Final summary
    cprint("\n" + "="*70, "green")
    cprint("🎉 AI WEBSITE REBUILD COMPLETED", "green", attrs=["bold"])
    cprint("="*70, "green")
    
    if saved_page_count > 0:
        cprint(f"[SUCCESS] {saved_page_count} HTML files were successfully generated and saved.", "green", attrs=["bold"])
        cprint(f"[SUCCESS] Output directory: {out_folder}", "green", attrs=["bold"])
        
        if failed_page_save_count > 0:
            cprint(f"[WARN] {failed_page_save_count} files encountered issues during saving.", "yellow")
        
        cprint("\n📁 Generated files include:", "cyan")
        cprint(f"  • global_styles.css (Global stylesheet)", "cyan")
        
        # List saved HTML files
        successfully_saved_files = [filename for filename in ai_response["html_files"].keys() 
                                  if isinstance(ai_response["html_files"][filename], str) 
                                  and filename.endswith(".html") 
                                  and "/" not in filename and "\\" not in filename][:5]
        
        for filename in successfully_saved_files:
            cprint(f"  • {filename} (Ready-to-deploy HTML page)", "cyan")
        if len(ai_response["html_files"]) > 5:
            cprint(f"  • ... and {len(ai_response['html_files']) - 5} more HTML file(s).", "cyan")
            
        cprint(f"  • original_crawled_data/ (Reference folder with original site data)", "cyan")
        
        # Check for index.html
        if "index.html" in successfully_saved_files:
            cprint(f"\n🚀 DEPLOYMENT READY: Your site has an index.html and is ready to deploy!", "green", attrs=["bold"])
            cprint(f"   Deploy to Vercel: Run 'vercel' in the {out_folder} directory", "cyan")
            cprint(f"   Or open {out_folder}/index.html in your browser to preview locally", "cyan")
        else:
            cprint(f"\n⚠️  Note: No index.html found. You may need to manually designate a main page for deployment.", "yellow")
        
    else:
        cprint(f"[ERROR] No HTML files were successfully saved from the AI response.", "red")
        if failed_page_save_count > 0:
            cprint(f"[INFO] {failed_page_save_count} files encountered issues during the saving process.", "yellow")
        sys.exit(1) # Indicate failure if no files saved

    # Atomic directory operation: move temp to final location
    cprint(f"\n[INFO] Finalizing output directory...", "cyan")
    try:
        # Handle existing final directory
        if os.path.exists(final_out_folder):
            backup_folder = final_out_folder + "_backup_" + str(int(os.path.getmtime(final_out_folder)))
            cprint(f"[INFO] Backing up existing directory to: {backup_folder}", "yellow")
            shutil.move(final_out_folder, backup_folder)
        
        # Atomic rename from temp to final
        shutil.move(out_folder, final_out_folder)
        cprint(f"[SUCCESS] Website successfully generated at: {final_out_folder}", "green", attrs=["bold"])
        
        # Update deployment instructions to use final folder
        if "index.html" in successfully_saved_files:
            cprint(f"\n🚀 DEPLOYMENT READY: Your site has an index.html and is ready to deploy!", "green", attrs=["bold"])
            cprint(f"   Deploy to Vercel: Run 'vercel' in the {final_out_folder} directory", "cyan")
            cprint(f"   Or open {final_out_folder}/index.html in your browser to preview locally", "cyan")
            
    except Exception as e:
        cprint(f"[ERROR] Failed to finalize output directory: {e}", "red")
        cprint(f"[INFO] Generated files are still available in temporary directory: {out_folder}", "yellow")
        sys.exit(1)

    cprint("="*70, "green")

if __name__ == "__main__":
    main() 