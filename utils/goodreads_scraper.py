"""
Test script to scrape your Goodreads shelf
Run: python test_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time

# Your shelf URL
SHELF_URL = "https://www.goodreads.com/review/list/121203593-philippe?shelf=bookclub2026nominees"

def scrape_shelf():
    """Scrape the shelf and get book data"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("🔍 Fetching shelf...")
    print(f"URL: {SHELF_URL}\n")
    
    try:
        response = requests.get(SHELF_URL, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Failed to fetch shelf")
            print(f"Response: {response.text[:500]}")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find book rows
        book_rows = soup.find_all('tr', class_='bookalike')
        
        if not book_rows:
            print("❌ No book rows found")
            print("Trying alternative selectors...")
            
            # Try alternative
            book_rows = soup.find_all('tr', id=re.compile(r'review_\d+'))
        
        print(f"✅ Found {len(book_rows)} book rows\n")
        
        if len(book_rows) == 0:
            # Debug: Save HTML to file
            with open('shelf_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("💾 Saved HTML to shelf_debug.html for inspection")
            return
        
        books = []
        
        for i, row in enumerate(book_rows, 1):
            try:
                book = {}
                
                # Title
                title_cell = row.find('td', class_='title')
                if title_cell:
                    title_link = title_cell.find('a', title=True)
                    if title_link:
                        book['title'] = title_link['title'].strip()
                        book['url'] = 'https://www.goodreads.com' + title_link['href']
                
                # Author
                author_cell = row.find('td', class_='author')
                if author_cell:
                    author_link = author_cell.find('a')
                    if author_link:
                        book['author'] = author_link.text.strip()
                
                # Cover
                cover_cell = row.find('td', class_='cover')
                if cover_cell:
                    img = cover_cell.find('img')
                    if img and 'src' in img.attrs:
                        cover_url = img['src']
                        # Upgrade to higher resolution
                        cover_url = cover_url.replace('._SX50_', '._SX318_')
                        cover_url = cover_url.replace('._SY75_', '._SY475_')
                        book['image_url'] = cover_url
                
                # Rating
                rating_cell = row.find('td', class_='avg_rating')
                if rating_cell:
                    rating_div = rating_cell.find('div', class_='value')
                    if rating_div:
                        book['rating'] = rating_div.text.strip()
                
                # Number of pages
                pages_cell = row.find('td', class_='num_pages')
                if pages_cell:
                    pages_div = pages_cell.find('div', class_='value')
                    if pages_div:
                        pages_text = pages_div.text.strip()
                        pages_match = re.search(r'(\d+)', pages_text)
                        if pages_match:
                            book['pages'] = pages_match.group(1)
                
                # Publication date
                pub_cell = row.find('td', class_='date_pub')
                if pub_cell:
                    pub_div = pub_cell.find('div', class_='value')
                    if pub_div:
                        pub_text = pub_div.text.strip()
                        # Extract year
                        year_match = re.search(r'\b(19|20)\d{2}\b', pub_text)
                        if year_match:
                            book['year'] = year_match.group(0)
                
                if book.get('title'):
                    books.append(book)
                    print(f"✓ [{i}] {book.get('title', 'Unknown')} by {book.get('author', 'Unknown')}")
                    print(f"    Pages: {book.get('pages', 'N/A')} | Year: {book.get('year', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Error parsing row {i}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully scraped {len(books)} books!")
        print(f"{'='*60}\n")
        
        # Save to JSON
        with open('scraped_books.json', 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        
        print("💾 Saved to scraped_books.json\n")
        
        # Display summary
        print("BOOK DATA SUMMARY:")
        print("-" * 60)
        for book in books:
            print(f"\nTitle: {book.get('title')}")
            print(f"Author: {book.get('author')}")
            print(f"Year: {book.get('year', 'N/A')}")
            print(f"Pages: {book.get('pages', 'N/A')}")
            print(f"Has Cover: {'Yes' if book.get('image_url') else 'No'}")
        
        return books
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("GOODREADS SHELF SCRAPER TEST")
    print("="*60 + "\n")
    
    books = scrape_shelf()
    
    print("\n" + "="*60)
    print("Done!")
    print("="*60)