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
        query = f"intitle:{book_title}+inauthor:{author}"
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
            print(f"No results found for '{book_title}' by {author}")
            return None
        
        # Get first book result
        book = data['items'][0]['volumeInfo']
        
        # Extract information
        book_info = {}
        
        # Get page count
        book_info['pages'] = str(book.get('pageCount', 'N/A'))
        
        # Get cover image (prefer high-res)
        image_links = book.get('imageLinks', {})
        book_info['image_url'] = (
            image_links.get('extraLarge') or
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
            description = re.sub('<[^<]+?>', '', description)
            book_info['summary'] = description[:500] + ('...' if len(description) > 500 else '')
        else:
            book_info['summary'] = 'No summary available'
        
        # Get Google Books link
        book_info['url'] = book.get('infoLink', '')
        
        # Get publisher and publish date
        book_info['publisher'] = book.get('publisher', 'N/A')
        book_info['published_date'] = book.get('publishedDate', 'N/A')
        
        # Get actual title and authors from API (for verification)
        book_info['api_title'] = book.get('title', book_title)
        book_info['api_authors'] = ', '.join(book.get('authors', [author]))
        
        print(f"✅ Found book data for '{book_info['api_title']}' by {book_info['api_authors']}")
        return book_info
    
    except requests.exceptions.RequestException as e:
        print(f"Google Books API request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing Google Books data: {str(e)}")
        return None

def fetch_book_data_openlibrary(book_title, author):
    '''Fetch book information from Open Library API (backup)'''
    try:
        # Open Library Search API
        base_url = "https://openlibrary.org/search.json"
        
        params = {
            'title': book_title,
            'author': author,
            'limit': 1
        }
        
        response = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'docs' not in data or len(data['docs']) == 0:
            return None
        
        book = data['docs'][0]
        
        # Extract information
        book_info = {}
        
        # Get cover image
        if 'cover_i' in book:
            book_info['image_url'] = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
        else:
            book_info['image_url'] = None
        
        # Get page count
        if 'number_of_pages_median' in book:
            book_info['pages'] = str(book['number_of_pages_median'])
        elif 'number_of_pages' in book:
            book_info['pages'] = str(book['number_of_pages'])
        else:
            book_info['pages'] = 'N/A'
        
        # Get first sentence as summary
        first_sentence = book.get('first_sentence', [''])[0] if 'first_sentence' in book else ''
        if first_sentence:
            book_info['summary'] = first_sentence[:500]
        else:
            book_info['summary'] = 'No summary available'
        
        # Get subjects as genres
        subjects = book.get('subject', [])
        if subjects:
            book_info['genres'] = ', '.join(subjects[:3])
        else:
            book_info['genres'] = 'N/A'
        
        # Get Open Library link
        if 'key' in book:
            book_info['url'] = f"https://openlibrary.org{book['key']}"
        else:
            book_info['url'] = ''
        
        # Get publisher and publish date
        book_info['publisher'] = book.get('publisher', ['N/A'])[0] if 'publisher' in book else 'N/A'
        book_info['published_date'] = str(book.get('first_publish_year', 'N/A'))
        
        print(f"✅ Found book data from Open Library")
        return book_info
    
    except Exception as e:
        print(f"Open Library API failed: {str(e)}")
        return None

def fetch_book_data_wikipedia(book_title, author):
    '''Fetch book information from Wikipedia API (fallback)'''
    try:
        # Wikipedia API endpoint
        base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        
        # Try searching with book title
        search_query = f"{book_title}_(novel)"
        page_url = base_url + search_query.replace(' ', '_')
        
        response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        
        # If not found with (novel), try just the title
        if response.status_code == 404:
            search_query = book_title
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
        
        # Try to extract page count from description
        pages_match = re.search(r'(\d+)\s*pages', summary, re.IGNORECASE)
        book_info['pages'] = pages_match.group(1) if pages_match else 'N/A'
        
        # Try to extract genre from description
        genre_keywords = ['fiction', 'novel', 'fantasy', 'science fiction', 'mystery', 
                         'thriller', 'romance', 'horror', 'historical', 'biography']
        
        found_genres = []
        summary_lower = summary.lower()
        for genre in genre_keywords:
            if genre in summary_lower:
                found_genres.append(genre.title())
                if len(found_genres) >= 2:
                    break
        
        book_info['genres'] = ', '.join(found_genres) if found_genres else 'N/A'
        book_info['publisher'] = 'N/A'
        book_info['published_date'] = 'N/A'
        
        return book_info
    except Exception as e:
        return None

def get_default_book_data():
    '''Return default book data when all APIs fail'''
    return {
        'pages': 'N/A',
        'image_url': None,
        'genres': 'N/A',
        'summary': 'No summary available',
        'url': None,
        'publisher': 'N/A',
        'published_date': 'N/A'
    }