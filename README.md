# Website Modernizer & AI Rebuilder

This project lets you crawl any website, extract its content (HTML, copy, images, CSS), and use Google Gemini AI to automatically modernize and rebuild the entire site holistically. The AI aims for improved copy, layout, design, responsiveness, and SEO, outputting a set of interlinked HTML pages and a global stylesheet.

---

## Features
- **Automated crawling**: Extracts major pages (configurable depth and max pages) from a given URL.
- **Content extraction**: Saves HTML, copy, images, and CSS for each crawled page.
- **Holistic AI-powered site remake**: Uses Google Gemini API (e.g., `gemini-2.5-flash-preview-05-20` or `gemini-1.5-pro-latest` with large context window) to process all crawled page data *at once*.
    - Aims to create a consistent design, shared navigation/header/footer structure.
    - Focuses on mobile-first responsiveness and SEO best practices.
    - Improves copy for clarity and engagement.
- **Structured AI Output**: The AI is prompted to return a JSON object containing:
    - A global CSS stylesheet (`global_styles.css`).
    - HTML content for each individual page, designed to work with the global styles and maintain consistency.
- **Plug-and-play output**: The `_ai` folder contains the remade site, with each page as an `index.html` in its respective subfolder, plus a `global_styles.css`.
- **Full context for site structure**: All crawled page information (HTML, CSS, copy, image URLs, page URLs) is aggregated and sent to Gemini in a single prompt to leverage its large context window (up to 1M tokens or more, depending on the model) for a cohesive rebuild.
- **Dashboard UI**: A Streamlit dashboard allows for easy URL input and process monitoring, with an experimental preview of the remade homepage.

---

## Prerequisites
- Python 3.9+
- Chrome browser and ChromeDriver (for Selenium)
- Google Gemini API key ([Get one here](https://ai.google.dev/gemini-api/docs/quickstart?lang=python))

---

## Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   - (Optional) For better Streamlit performance, install watchdog:
     ```bash
     pip install watchdog
     ```

3. **Set up your Gemini API key**
   - Create a file named `.env.local` in the project root:
     ```
     GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
     ```
   - Alternatively, set the `GOOGLE_GEMINI_API_KEY` environment variable.

---

## Usage

### 1. Crawl a Website
Extracts content and saves it in a structured folder.
```bash
python crawl_site.py https://example.com --max_pages 10 --depth 1
```
- Output: A folder named after the domain (e.g., `example.com/`) with subfolders for each page.
- CLI arguments `--max_pages` and `--depth` are available.

### 2. AI-Powered Remake (Entire Site)
Reads all extracted data from the crawl folder and uses Gemini to generate a modernized version of the entire site.
```bash
python remake_site_with_ai.py example.com --model gemini-2.5-flash-preview-05-20
```
- `--model`: Specify the Gemini model to use (default: `gemini-2.5-flash-preview-05-20`).
- Output: A new folder (e.g., `example.com_ai/`) containing:
    - `global_styles.css`: A stylesheet for the entire remade site.
    - Subfolders for each page (e.g., `home/`, `about/`) each containing an `index.html` and original reference files.

### 3. Dashboard (Streamlit UI)
Run the dashboard for an interactive experience:
```bash
streamlit run dashboard.py
```
- Enter a website URL. The dashboard will run the crawl and then the AI remake process.
- Logs are displayed, and an experimental preview of the remade homepage might be shown upon completion.

---

## Output Structure
```
example.com/                 # Crawled data
  home/
    url.txt
    page.html
    copy.txt
    images.txt
    css.txt
  about/
    ...
example.com_ai/              # AI Remade Site
  global_styles.css          # CSS for the whole site
  home/
    index.html               # Modernized, ready-to-use HTML for home
    original_url.txt         # Original files copied for reference
    original_page.html
    original_copy.txt
    original_images.txt
    original_css.txt
  about/
    index.html
    (original files...)
  ...
```

---

## Model & Prompting
- Default model for remake: `gemini-2.5-flash-preview-05-20` (configurable via `--model` argument). `gemini-1.5-pro-latest` is also a good option for its large context window.
- **All crawled page data** (HTML, CSS, copy, image URLs) is aggregated and sent to Gemini in a single, comprehensive prompt.
- The prompt instructs Gemini to:
    - Rebuild the *entire site* cohesively.
    - Ensure mobile-first responsiveness and SEO optimization.
    - Maintain brand theme and improve copy.
    - Design conceptually shared components (header, footer, nav) for consistency.
    - Output a JSON object containing a global CSS string and HTML strings for each page.
- **Streaming output is not currently implemented for the AI generation part.** The full result is processed after Gemini responds.

---

## Notes
- **Data Sent to Gemini:** The `remake_site_with_ai.py` script sends aggregated content from all crawled pages to the Google Gemini API.
- **Process Steps:** Crawling and AI remake are sequential.
- **Configuration:**
    - `crawl_site.py`: `MAX_PAGES`, `CRAWL_DEPTH` via CLI args.
    - `remake_site_with_ai.py`: Gemini model via CLI arg `--model`.
- **Token Limits:** While models like `gemini-1.5-pro-latest` and potentially `gemini-2.5-flash-preview-05-20` offer very large context windows (1M+ tokens), extremely large or numerous crawled pages could still exceed these limits. The script currently sends all data; future improvements might involve summarization or chunking if limits are hit.

---

## Troubleshooting
- **Missing Modules:** Run `pip install -r requirements.txt` in your virtual environment.
- **Selenium/ChromeDriver:** Ensure ChromeDriver is installed, in PATH, and matches your Chrome version.
- **Gemini API Key:** Verify `GOOGLE_GEMINI_API_KEY` in `.env.local` or as an environment variable.
- **Gemini API Errors:**
    - Check error messages for specifics (e.g., quota, model name, content blocking).
    - If "JSONDecodeError" occurs, the model might not have output valid JSON. Check the debug logs for raw Gemini output. The prompt strongly requests JSON, but model adherence can vary.
    - Context window limits: If the input is too large, the API might reject the request.
- **Dashboard Preview:** The HTML preview in Streamlit is experimental. For an accurate view, open the generated `index.html` files in a web browser. Ensure `global_styles.css` is correctly linked and present.

---

## License
MIT License 