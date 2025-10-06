import requests
import streamlit as st
from config.settings import REQUEST_TIMEOUT
import re

def fetch_book_data_wikipedia(book_title, author):
    '''Fetch book information from Wikipedia API'''
    try:
        # Wikipedia API endpoint
        base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        
        # Try searching with book title
        search_query = f"{book_title}_(novel)"  # Many books have (novel) suffix
        page_url = base_url + search_query.replace(' ', '_')
        
        response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        
        # If not found with (novel), try just the title
        if response.status_code == 404:
            search_query = book_title
            page_url = base_url + search_query.replace(' ', '_')
            response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        
        # If still not found, try with author name
        if response.status_code == 404:
            search_query = f"{book_title}_by_{author}"
            page_url = base_url + search_query.replace(' ', '_')
            response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # Extract information
        book_info = {}
        
        # Get cover image
        if 'thumbnail' in data:
            book_info['image_url'] = data['thumbnail'].get('source')
        elif 'originalimage' in data:
            book_info['image_url'] = data['originalimage'].get('source')
        else:
            book_info['image_url'] = None
        
        # Get summary/description
        summary = data.get('extract', '')
        if summary:
            book_info['summary'] = summary[:500] + ('...' if len(summary) > 500 else '')
        else:
            book_info['summary'] = 'No summary available'
        
        # Get Wikipedia URL
        book_info['url'] = data.get('content_urls', {}).get('desktop', {}).get('page', '')
        
        # Try to extract page count from description (often mentioned)
        pages_match = re.search(r'(\d+)\s*pages', summary, re.IGNORECASE)
        if pages_match:
            book_info['pages'] = pages_match.group(1)
        else:
            book_info['pages'] = 'N/A'
        
        # Try to extract genre from description
        genre_keywords = ['fiction', 'novel', 'fantasy', 'science fiction', 'mystery', 
                         'thriller', 'romance', 'horror', 'historical', 'biography',
                         'non-fiction', 'memoir', 'poetry', 'drama']
        
        found_genres = []
        summary_lower = summary.lower()
        for genre in genre_keywords:
            if genre in summary_lower:
                found_genres.append(genre.title())
                if len(found_genres) >= 2:
                    break
        
        book_info['genres'] = ', '.join(found_genres) if found_genres else 'N/A'
        
        # Additional info
        book_info['publisher'] = 'N/A'
        book_info['published_date'] = 'N/A'
        
        return book_info
    
    except Exception as e:
        st.warning(f"Could not fetch data from Wikipedia: {str(e)}")
        return None

def get_default_book_data():
    '''Return default book data when API fetch fails'''
    return {
        'pages': 'N/A',
        'image_url': None,
        'genres': 'N/A',
        'summary': 'No summary available',
        'url': None,
        'publisher': 'N/A',
        'published_date': 'N/A'
    }