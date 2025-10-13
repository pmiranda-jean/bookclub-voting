"""
Standalone script to test book APIs
Run this locally: python test_book_apis.py
"""

import requests
import json

def test_google_books(title, author):
    """Test Google Books API"""
    print(f"\n{'='*60}")
    print(f"Testing Google Books API")
    print(f"Searching: '{title}' by {author}")
    print(f"{'='*60}")
    
    try:
        base_url = "https://www.googleapis.com/books/v1/volumes"
        query = f"intitle:{title}+inauthor:{author}"
        params = {
            'q': query,
            'maxResults': 1,
            'printType': 'books'
        }
        
        print(f"URL: {base_url}?q={query}")
        
        response = requests.get(base_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                book = data['items'][0]['volumeInfo']
                
                print(f"\n✅ SUCCESS! Found book:")
                print(f"  Title: {book.get('title', 'N/A')}")
                print(f"  Authors: {', '.join(book.get('authors', ['N/A']))}")
                print(f"  Pages: {book.get('pageCount', 'N/A')}")
                print(f"  Categories: {', '.join(book.get('categories', ['N/A']))}")
                print(f"  Publisher: {book.get('publisher', 'N/A')}")
                print(f"  Published: {book.get('publishedDate', 'N/A')}")
                
                # Check for images
                image_links = book.get('imageLinks', {})
                if image_links:
                    print(f"  Image URL: {image_links.get('thumbnail', 'N/A')}")
                else:
                    print(f"  Image URL: None")
                
                # Check for description
                description = book.get('description', '')
                if description:
                    print(f"  Description: {description[:100]}...")
                else:
                    print(f"  Description: None")
                
                return True
            else:
                print(f"\n❌ No results found")
                return False
        else:
            print(f"\n❌ API request failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_open_library(title, author):
    """Test Open Library API"""
    print(f"\n{'='*60}")
    print(f"Testing Open Library API")
    print(f"Searching: '{title}' by {author}")
    print(f"{'='*60}")
    
    try:
        base_url = "https://openlibrary.org/search.json"
        params = {
            'title': title,
            'author': author,
            'limit': 1
        }
        
        print(f"URL: {base_url}")
        
        response = requests.get(base_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'docs' in data and len(data['docs']) > 0:
                book = data['docs'][0]
                
                print(f"\n✅ SUCCESS! Found book:")
                print(f"  Title: {book.get('title', 'N/A')}")
                print(f"  Author: {', '.join(book.get('author_name', ['N/A']))}")
                print(f"  Pages: {book.get('number_of_pages_median', 'N/A')}")
                print(f"  First Published: {book.get('first_publish_year', 'N/A')}")
                
                # Check for cover
                if 'cover_i' in book:
                    cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
                    print(f"  Cover URL: {cover_url}")
                else:
                    print(f"  Cover URL: None")
                
                # Check for subjects
                subjects = book.get('subject', [])
                if subjects:
                    print(f"  Subjects: {', '.join(subjects[:3])}")
                else:
                    print(f"  Subjects: None")
                
                return True
            else:
                print(f"\n❌ No results found")
                return False
        else:
            print(f"\n❌ API request failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_wikipedia(title):
    """Test Wikipedia API"""
    print(f"\n{'='*60}")
    print(f"Testing Wikipedia API")
    print(f"Searching: '{title}'")
    print(f"{'='*60}")
    
    try:
        base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        search_query = f"{title}_(novel)"
        page_url = base_url + search_query.replace(' ', '_')
        
        print(f"URL: {page_url}")
        
        response = requests.get(page_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SUCCESS! Found page:")
            print(f"  Title: {data.get('title', 'N/A')}")
            print(f"  Extract: {data.get('extract', 'N/A')[:100]}...")
            
            if 'thumbnail' in data:
                print(f"  Thumbnail: {data['thumbnail']['source']}")
            else:
                print(f"  Thumbnail: None")
            
            return True
        else:
            print(f"\n❌ Page not found")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("BOOK API TESTER")
    print("="*60)
    
    # Test cases
    test_books = [
        ("1984", "George Orwell"),
        ("Harry Potter and the Philosopher's Stone", "J.K. Rowling"),
        ("The Great Gatsby", "F. Scott Fitzgerald"),
        ("To Kill a Mockingbird", "Harper Lee")
    ]
    
    for title, author in test_books:
        print(f"\n\n{'#'*60}")
        print(f"Testing: '{title}' by {author}")
        print(f"{'#'*60}")
        
        google_success = test_google_books(title, author)
        openlibrary_success = test_open_library(title, author)
        wikipedia_success = test_wikipedia(title)
        
        print(f"\n{'='*60}")
        print(f"RESULTS for '{title}':")
        print(f"  Google Books: {'✅' if google_success else '❌'}")
        print(f"  Open Library: {'✅' if openlibrary_success else '❌'}")
        print(f"  Wikipedia: {'✅' if wikipedia_success else '❌'}")
        print(f"{'='*60}")
    
    print("\n\nDone! Check results above.")