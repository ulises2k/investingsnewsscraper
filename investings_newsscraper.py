from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import asyncio
import time
import json
import os
from urllib.parse import urlparse, urljoin

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def identify_category(soup, url, debug=False):
    """Extract category using enhanced logic from single_article_scraper"""
    category = "Unknown Category"

    # Method 1: From breadcrumbs
    breadcrumbs = soup.select("a.breadcrumbs")
    if breadcrumbs:
        category = breadcrumbs[-1].text.strip()
        if debug:
            print(f"Found category from breadcrumbs: {category}")

    # Method 2: From URL path segments for economy category
    if category == "Unknown Category" or category.lower() == "news":
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            # Check specifically for economy-news in the path
            if "economy-news" in parsed_url.path:
                category = "Economy"
                if debug:
                    print(f"Found 'Economy' category from URL path")
            # Otherwise use the second part of the path if it's not "news"
            elif len(path_parts) >= 2 and path_parts[1] != "news":
                category = path_parts[1].replace("-", " ").title()
                if debug:
                    print(f"Derived category from URL path part: {category}")

    # Method 3: From navigation elements
    if category == "Unknown Category" or category.lower() == "news":
        nav_elements = soup.select("nav a")
        for element in nav_elements:
            if "news" in element.get("href", "").lower() and element.text.strip():
                category = element.text.strip()
                if debug:
                    print(f"Found category from nav: {category}")
                break

    return category


def extract_full_text(soup, debug=False):
    """Extract full text using enhanced logic from single_article_scraper"""
    paragraphs = []

    # Primero intentamos encontrar el contenedor con id="article"
    article_container = soup.find(id="article")
    if article_container:
        paragraphs = article_container.find_all("p")
        if debug:
            print(f"Found {len(paragraphs)} paragraphs inside #article container.")
    else:
        # Try multiple possible selectors for article content
        content_selectors = [
            "div.articlePage p",
            "div.WYSIWYG p",
            "div.articleText p",
            "div.content-section p",
            "article p",
            "p",  # Fallback to any paragraph
        ]

        for selector in content_selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                if debug:
                    print(f"Found {len(paragraphs)} paragraphs using selector: {selector}")
                break

    # Filtrar párrafos irrelevantes (muy cortos) y excluir el último
    filtered_paragraphs = [
        p for p in paragraphs[:-1] if len(p.get_text(strip=True)) > 20
    ]

    # Unir el texto
    full_text = " ".join(p.get_text(strip=True) for p in filtered_paragraphs)

    return full_text



async def scrape_article(session, link, debug=False):
    """Scrape a single article with improved handling from single_article_scraper"""
    try:
        response = await session.get(
            link,
            impersonate="chrome124",
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.investing.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            },
        )

        if response.status_code != 200:
            print(f"Failed to retrieve article: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title
        title_elem = soup.find("h1")
        if not title_elem:
            title_elem = soup.find("h1", {"class": lambda x: x and "text-" in x})
        title = title_elem.text.strip() if title_elem else "Unknown headline"

        # Extract category using enhanced method
        category = identify_category(soup, link, debug)

        # Extract full text using enhanced method
        full_text = extract_full_text(soup, debug)

        return {
            "headline": title,
            "category": category,
            "full_text": full_text,
            "url": link,
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except Exception as e:
        print(f"Error scraping {link}: {str(e)}")
        return None

def load_existing_data(filename="news_data.json"):
    """Load existing article data from file if it exists"""
    try:
        if os.path.exists(os.path.join(__location__, filename)):
            with open(os.path.join(__location__, filename), "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading existing data: {str(e)}")
        return []

def save_to_json(data, filename="news_data.json"):
    """Save the article data to a JSON file"""
    with open(os.path.join(__location__, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Article data saved to {filename}")

async def main():
    # Command line argument for debug mode
    import argparse

    parser = argparse.ArgumentParser(description="Scrape investment news articles")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    # Load existing data
    existing_data = load_existing_data()
    existing_urls = {item["url"] for item in existing_data}

    print(f"Found {len(existing_data)} existing articles")

    async with AsyncSession() as session:
        # Initial request with proper headers
        response = await session.get(
            "https://www.investing.com/news/latest-news",
            impersonate="chrome124",
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.investing.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            },
        )

        soup = BeautifulSoup(response.content, "html.parser")
        cards = soup.find_all(
            "li",
            class_="flex items-center !mt-0 border-t border-solid border-[#E6E9EB] py-6",
        )

        # Track new articles
        new_articles = 0
        processed_count = 0

        for i, card in enumerate(cards):
            try:
                # Buscar el enlace dentro de la tarjeta
                link_elem = card.find("a", href=True)
                if not link_elem:
                    continue

                # Obtener el enlace completo
                relative_link = link_elem.get("href")
                link = urljoin("https://www.investing.com", relative_link)

                # Verificar si ya fue procesado
                if link in existing_urls:
                    continue

                # Obtener el título del artículo
                title = link_elem.get_text(strip=True)
                if not title:
                    continue

                # Scrape article details with error handling
                article_data = await scrape_article(session, link, args.debug)
                if not article_data:
                    continue

                # Add to existing data
                existing_data.append(article_data)
                existing_urls.add(link)
                new_articles += 1
                processed_count += 1

                print(
                    f"Scraped article {processed_count}: {article_data['headline']} ({article_data['category']})"
                )

                # Save after each successful scrape for resilience
                if new_articles % 5 == 0:
                    save_to_json(existing_data)
                    print(f"Intermediate save: {new_articles} new articles scraped")

                # Proper async delay between requests
                if i < len(cards) - 1:
                    await asyncio.sleep(2)  # Respectful delay

            except Exception as e:
                print(f"Error processing card {i}: {str(e)}")
                continue

        # Final save
        save_to_json(existing_data)
        print(
            f"Completed: {new_articles} new articles added, total: {len(existing_data)}"
        )


if __name__ == "__main__":
    asyncio.run(main())
