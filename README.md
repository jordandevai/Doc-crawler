# Web Crawler - Document Processor

A robust, well-designed web crawler UI built with Python and PyQt6 that crawls websites and converts content to AI-friendly Markdown format.

## Features

- **Intuitive PyQt6 GUI**: Clean, responsive desktop interface
- **Robust Web Crawling**: Respects robots.txt, handles errors gracefully
- **Markdown Conversion**: Converts HTML to clean, structured Markdown
- **Multi-threaded**: Non-blocking UI with background crawling
- **Configurable**: Adjustable crawl depth, delay, and robots.txt compliance
- **Export Functionality**: Save crawled content to Markdown files

## Architecture

The application follows a modular, layered architecture with high-performance asynchronous processing:

```
UI (PyQt6) → Orchestrator (QThread Worker) → Async Crawler → Processor → Output
```

- **UI Layer**: `src/ui/main_window.py` - Real-time user interface with live feedback
- **Orchestrator Layer**: `src/workers/crawl_worker.py` - Asyncio event loop management
- **Service Layer**: 
  - `src/core/crawler.py` - Asynchronous concurrent web crawling
  - `src/core/processor.py` - HTML to Markdown conversion
- **Entry Point**: `main.py` - Application initialization

## Installation & Quick Start

### Option 1: One-Command Launch (Recommended)

**Linux/macOS:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

The launcher script automatically:
- Creates a virtual environment (if needed)
- Installs dependencies (if needed)
- Runs the application

### Option 2: Manual Setup

1. **Clone or download the project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Dependencies

- **PyQt6** (≥6.6.0): GUI framework
- **httpx** (≥0.27.0): Modern HTTP client
- **beautifulsoup4** (≥4.12.3): HTML parsing
- **lxml** (≥5.2.2): Fast XML/HTML parser
- **markdownify** (≥0.12.1): HTML to Markdown conversion

## Usage

1. **Enter Target URL**: Input the website URL to crawl
2. **Configure Settings**:
   - **Max Depth**: How many levels deep to crawl (1-10)
   - **Delay**: Seconds between requests (0-60)
   - **Respect robots.txt**: Enable/disable robots.txt compliance
3. **Start Crawling**: Click "Start Crawl" to begin
4. **Monitor Progress**: Real-time progress updates and content preview
5. **Save Results**: Export crawled content to Markdown file

## Key Benefits

- **High Performance**: Asynchronous concurrent crawling with up to 10x speed improvement
- **Real-Time Feedback**: Live UI updates as pages are processed
- **Instant Cancellation**: Responsive stop functionality 
- **AI-Friendly Output**: Clean Markdown format optimized for language models
- **Token Efficient**: Minimal syntactic overhead compared to HTML
- **Human Readable**: Easy to review and edit output
- **Robust Error Handling**: Graceful handling of network issues and malformed HTML
- **Respectful Crawling**: Honors robots.txt and implements delays

## File Structure

```
Doc-crawler/
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
├── run.sh                  # Linux/macOS launcher script
├── run.bat                 # Windows launcher script
├── README.md               # Documentation
├── .gitignore              # Git ignore rules
└── src/                    # Source code directory
    ├── ui/
    │   ├── __init__.py
    │   └── main_window.py  # Main PyQt6 window
    ├── core/
    │   ├── __init__.py
    │   ├── crawler.py      # Web crawling logic
    │   └── processor.py    # Content processing
    └── workers/
        ├── __init__.py
        └── crawl_worker.py # Background thread worker
```

## Example Workflow

1. User enters `https://docs.python.org/3/` with max depth 2
2. Crawler fetches the page, respects robots.txt, extracts links
3. Processor converts HTML content to clean Markdown
4. UI displays real-time progress and content preview
5. User saves combined results to `crawled_content.md`

## Technical Highlights

- **Thread Safety**: Uses Qt's signals/slots for safe cross-thread communication
- **Memory Efficient**: Processes pages incrementally, not all at once
- **Error Resilient**: Continues crawling even if individual pages fail
- **Modular Design**: Easy to extend or modify individual components
- **Production Ready**: Comprehensive error handling and user feedback