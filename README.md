# Investing.com News Scraper

An asynchronous web scraper designed to extract latest news articles from Investing.com. This tool helps collect financial news data for analysis, research, or monitoring market trends.

## Features

- **Asynchronous Scraping**: Uses `curl_cffi` for fast, non-blocking HTTP requests
- **Intelligent Category Detection**: Multi-method approach to identify article categories
- **Content Extraction**: Pulls full article text with smart filtering
- **Duplicate Prevention**: Skips already scraped articles
- **Resilient Storage**: Regular saves to prevent data loss
- **Respectful Crawling**: Built-in delays to avoid overloading the target site

## Requirements

```
beautifulsoup4
curl_cffi
asyncio
```

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install beautifulsoup4 curl_cffi
```

## Usage

Run the script with Python:

```bash
python investings_newsscraper.py
```

For debugging information:

```bash
python investings_newsscraper.py --debug
```

## Data Output

The script saves data to `news_data.json` with the following structure:

```json
[
  {
    "headline": "Article Title",
    "category": "Article Category",
    "full_text": "Complete article content...",
    "url": "https://www.investing.com/article-url",
    "scraped_at": "2025-04-13T12:34:56Z"
  }
]
```

## How It Works

1. Fetches the latest news page from Investing.com
2. Identifies new articles not previously scraped
3. For each new article:
   - Extracts the headline, category, and full text content
   - Uses multiple methods to accurately identify the article category
   - Saves data periodically to prevent loss

## Key Components

### Category Identification
The scraper uses three different methods to identify article categories:
- Extracts from breadcrumbs navigation
- Analyzes URL structure and path segments
- Searches navigation elements when other methods fail

### Text Extraction
Articles are processed to:
- Extract meaningful paragraphs
- Filter out non-article content
- Remove short placeholder text

## Notes

- This scraper is designed for educational and research purposes only
- Please respect Investing.com's terms of service and robots.txt
- Consider implementing additional rate limiting for production use

## License

MIT License