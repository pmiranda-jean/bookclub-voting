import requests
from bs4 import BeautifulSoup
import streamlit as st
from config.settings import REQUEST_TIMEOUT, USER_AGENT

def scrape_goodreads(book_title, author):
    '''Scrape book information from Goodreads'''
    try:
        # Search URL
        search_query = f"{book_title} {author}".replace(' ', '+')
        search_url = f"https://www.goodreads.com/search?q={search_query}"
        
        headers = {'User-Agent': USER_AGENT}
        
        response = requests.get(search_url, headers=headers, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find first book result
        book_link = soup.find('a', class_='bookTitle')
        if not book_link:
            return None
        
        book_url = 'https://www.goodreads.com' + book_link['href']
        
        # Get book page
        book_response = requests.get(book_url, headers=headers, timeout=REQUEST_TIMEOUT)
        book_soup = BeautifulSoup(book_response.content, 'html.parser')
        
        # Extract information
        book_info = {'url': book_url}
        
        # Get cover image
        img_tag = book_soup.find('img', class_='ResponsiveImage')
        if img_tag and img_tag.get('src'):
            book_info['image_url'] = img_tag['src']
        else:
            book_info['image_url'] = None
        
        # Get pages
        pages = book_soup.find('p', {'data-testid': 'pagesFormat'})
        if pages:
            book_info['pages'] = pages.text.strip().split()[0]
        else:
            book_info['pages'] = 'N/A'
        
        # Get genres
        genre_elements = book_soup.find_all('span', class_='BookPageMetadataSection__genreButton')
        if genre_elements:
            book_info['genres'] = ', '.join([g.text.strip() for g in genre_elements[:3]])
        else:
            book_info['genres'] = 'N/A'
        
        # Get summary
        summary = book_soup.find('div', class_='DetailsLayoutRightParagraph')
        if summary:
            book_info['summary'] = summary.get_text(strip=True)[:500] + '...'
        else:
            book_info['summary'] = 'No summary available'
        
        return book_info
    
    except Exception as e:
        st.warning(f"Could not fetch data from Goodreads: {str(e)}")
        return None

def get_default_book_data():
    '''Return default book data when scraping fails'''
    return {
        'pages': 'N/A',
        'image_url': None,
        'genres': 'N/A',
        'summary': 'No summary available',
        'url': None
    }
