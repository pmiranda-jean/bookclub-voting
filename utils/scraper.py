import requests
import streamlit as st
from config.settings import REQUEST_TIMEOUT
import re 

def fetch_book_data_google(book_title, author):
    '''Fetch book information from Google Books API'''
    try:
        # Google Books API endpoint
        base_url = "https://www.googleapis.com/books/v1/volumes"
        
        # Build search query
        #query = f"intitle:{book_title}+inauthor:{author}"
        query = f"{book_title} {author}"
        params = {
            'q': query,
            'maxResults': 1,
            'printType': 'books'
        }
        
        response = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if we got results
        if 'items' not in data or len(data['items']) == 0:
            return None
        
        # Get first book result
        book = data['items'][0]['volumeInfo']
        
        # Extract information
        book_info = {}
        
        # Get title and authors (for confirmation)
        book_info['api_title'] = book.get('title', book_title)
        book_info['api_authors'] = ', '.join(book.get('authors', [author]))
        
        # Get page count
        book_info['pages'] = str(book.get('pageCount', 'N/A'))
        
        # Get cover image (prefer high-res)
        image_links = book.get('imageLinks', {})
        book_info['image_url'] = (
            image_links.get('large') or 
            image_links.get('medium') or 
            image_links.get('thumbnail') or 
            image_links.get('smallThumbnail')
        )
        
        # Get categories/genres
        categories = book.get('categories', [])
        if categories:
            book_info['genres'] = ', '.join(categories[:3])
        else:
            book_info['genres'] = 'N/A'
        
        # Get description/summary
        description = book.get('description', '')
        if description:
            # Remove HTML tags if present
            import re
            description = re.sub('<[^<]+?>', '', description)
            book_info['summary'] = description[:500] + ('...' if len(description) > 500 else '')
        else:
            book_info['summary'] = 'No summary available'
        
        # Get Google Books link
        book_info['url'] = book.get('infoLink', '')
        
        # Get publisher and publish date (bonus info)
        book_info['publisher'] = book.get('publisher', 'N/A')
        book_info['published_date'] = book.get('publishedDate', 'N/A')
        
        return book_info
    
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch data from Google Books: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"Error processing book data: {str(e)}")
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