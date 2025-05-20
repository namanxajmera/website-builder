# Website Modernizer & AI Rebuilder

This project lets you crawl any website, extract its content (HTML, copy, images, CSS), and use Google Gemini AI to automatically modernize and rebuild the site with improved copy, layout, and design. The output is a plug-and-play, ready-to-deploy HTML site that maintains the original brand theme and assets.

---

## Features
- **Automated crawling**: Extracts all major pages (up to 2 levels deep) from a given URL.
- **Content extraction**: Saves HTML, copy, images, and CSS for each page.
- **AI-powered site remake**: Uses Google Gemini API to generate modern, responsive HTML+CSS for each page, improving copy and design while preserving brand identity.
- **Plug-and-play output**: Each page is output as a ready-to-deploy `index.html`.

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

3. **Set up your Gemini API key**
   - Create a file named `.env.local` in the project root:
     ```
     GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
     ```

---

## Usage

### 1. Crawl a Website
Extracts all content and saves it in a structured folder.

```bash
python crawl_site.py https://example.com
```
- Output: A folder named after the domain (e.g., `example.com/`) with subfolders for each page.

### 2. AI-Powered Remake
Reads the extracted data and generates modern HTML+CSS for each page using Gemini.

```bash
python remake_site_with_ai.py example.com
```
- Output: A new folder (e.g., `example.com_ai/`) with `index.html` for each page, ready to deploy.

---

## Output Structure
```
example.com/
  home/
    url.txt
    page.html
    copy.txt
    images.txt
    css.txt
  about/
    ...
example.com_ai/
  home/
    index.html   # Modernized, ready-to-use HTML
    (original files for reference)
  about/
    ...
```

---

## Model & Prompting
- Uses the latest Gemini model (e.g., `gemini-2.5-pro-preview-05-06` or `gemini-2.5-flash-preview-04-17`).
- Sends original copy, CSS, HTML, and image URLs to Gemini.
- Prompts Gemini to rebuild each page as a modern, visually appealing, responsive HTML+CSS file, maintaining brand theme and improving copy.

---

## Notes
- **No data is sent to Gemini unless you run the AI enhancement step.**
- **You can run the crawl and AI steps independently.**
- **Supports up to 20 pages per site by default (configurable in `crawl_site.py`).**

---

## Troubleshooting
- If you see errors about missing modules, run `pip install -r requirements.txt` in your virtual environment.
- If Selenium fails, ensure ChromeDriver is installed and matches your Chrome version.
- If Gemini API fails, check your API key in `.env.local`.

---

## License
MIT License 