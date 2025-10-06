import requests
import streamlit as st
from config.settings import REQUEST_TIMEOUT
import re 

import requests
import re
# Assuming REQUEST_TIMEOUT and st (streamlit) are defined globally

def fetch_book_data_google(book_title, author):
    '''Fetch book information from Google Books API with FULL projection'''
    
    # 🚨 NOTE: For best results, consider modifying the user input validation
    # to treat an ISBN as a high-priority search query.
    
    try:
        base_url = "https://www.googleapis.com/books/v1/volumes"
        
        # Use a flexible query for robustness in a live environment
        query = f"{book_title} {author}"
        
        params = {
            'q': query,
            'maxResults': 1,
            'printType': 'books',
            'projection': 'full' # <--- Request ALL available metadata
        }
        
        response = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            return None
        
        # Get first book result (volumeInfo)
        book = data['items'][0]['volumeInfo']
        
        book_info = {}
        
        # Core Info
        book_info['api_title'] = book.get('title', book_title)
        book_info['api_authors'] = ', '.join(book.get('authors', [author]))
        
        # 🟢 IMPROVED PAGE COUNT (Handles both missing key and None value)
        page_count = book.get('pageCount')
        book_info['pages'] = str(page_count) if page_count is not None else 'N/A'
        
        # 🟢 IMPROVED GENRES (Robust check for list existence and content)
        categories = book.get('categories', [])
        if categories and isinstance(categories, list) and len(categories) > 0:
            book_info['genres'] = ', '.join(categories[:3])
        else:
            book_info['genres'] = 'N/A'
            
        # Cover Image (Still using your excellent prioritized fallback logic)
        image_links = book.get('imageLinks', {})
        book_info['image_url'] = (
            image_links.get('large') or 
            image_links.get('medium') or 
            image_links.get('thumbnail') or 
            image_links.get('smallThumbnail')
        )
        
        # Summary/Description
        description = book.get('description', '')
        if description:
            description = re.sub('<[^<]+?>', '', description)
            book_info['summary'] = description[:500] + ('...' if len(description) > 500 else '')
        else:
            book_info['summary'] = 'No summary available'
        
        # Other Info
        book_info['url'] = book.get('infoLink', '')
        book_info['publisher'] = book.get('publisher', 'N/A')
        book_info['published_date'] = book.get('publishedDate', 'N/A')
        
        return book_info
    
    except requests.exceptions.RequestException as e:
        # Use st.warning if you are in a Streamlit app environment
        # st.warning(f"Could not fetch data from Google Books: {str(e)}")
        print(f"Could not fetch data from Google Books: {str(e)}") # Fallback for non-streamlit
        return None
    except Exception as e:
        # st.warning(f"Error processing book data: {str(e)}")
        print(f"Error processing book data: {str(e)}") # Fallback for non-streamlit
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
