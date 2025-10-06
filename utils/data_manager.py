import json
import os
from datetime import datetime

def ensure_data_directory():
    '''Create data directory if it doesn't exist'''
    if not os.path.exists('data'):
        os.makedirs('data')

def load_books(filepath='data/books.json'):
    '''Load books from JSON file'''
    ensure_data_directory()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading books: {e}")
            return []
    return []

def save_books(books, filepath='data/books.json'):
    '''Save books to JSON file'''
    ensure_data_directory()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving books: {e}")

def load_votes(filepath='data/votes.json'):
    '''Load votes from JSON file'''
    ensure_data_directory()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading votes: {e}")
            return []
    return []

def save_votes(votes, filepath='data/votes.json'):
    '''Save votes to JSON file'''
    ensure_data_directory()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(votes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving votes: {e}")

def add_book(books, title, author, submitter):
    '''Add a new book to the list'''
    book_entry = {
        'title': title,
        'author': author,
        'submitter': submitter,
        'timestamp': datetime.now().isoformat()
    }
    books.append(book_entry)
    return book_entry

def book_exists(books, title, author):
    '''Check if a book already exists'''
    return any(b['title'].lower() == title.lower() and 
               b['author'].lower() == author.lower() 
               for b in books)

def add_vote(votes, voter, vote_data):
    '''Add a new vote'''
    vote_entry = {
        'voter': voter,
        'votes': vote_data,
        'timestamp': datetime.now().isoformat()
    }
    votes.append(vote_entry)
    return vote_entry

def has_voted(votes, voter_name):
    '''Check if a person has already voted'''
    return any(v['voter'] == voter_name for v in votes)

def calculate_scores(votes):
    '''Calculate total points for each book'''
    book_scores = {}
    for vote in votes:
        for book_idx, points in vote['votes']:
            if book_idx not in book_scores:
                book_scores[book_idx] = 0
            book_scores[book_idx] += points
    return book_scores

def get_top_books(book_scores, n=6):
    '''Get top N books by score'''
    return sorted(book_scores.items(), key=lambda x: x[1], reverse=True)[:n]

def export_all_data(books, votes):
    '''Export all data as JSON string'''
    return json.dumps({
        'books': books,
        'votes': votes,
        'exported_at': datetime.now().isoformat()
    }, indent=2, ensure_ascii=False)

def import_data(json_string):
    '''Import data from JSON string'''
    try:
        data = json.loads(json_string)
        return data.get('books', []), data.get('votes', [])
    except:
        return None, None
