import json
import os
from datetime import datetime
import streamlit as st
import requests
import base64

def ensure_data_directory():
    '''Create data directory if it doesn't exist'''
    if not os.path.exists('data'):
        os.makedirs('data')

def commit_to_github(file_path, commit_message):
    '''Commit and push a file to GitHub using GitHub API'''
    try:
        # Get GitHub credentials from Streamlit secrets
        if "github" not in st.secrets:
            st.warning("⚠️ GitHub secrets not configured - data saved locally only")
            print("GitHub secrets not configured")
            return False
        
        token = st.secrets["github"]["token"]
        username = st.secrets["github"]["username"]
        repo = st.secrets["github"]["repo"]
        
        print(f"🔧 Attempting to commit {file_path} to {username}/{repo}")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{file_path}"
        
        # Get the current file SHA (required for updates)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        print(f"📡 Fetching current file from GitHub...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            sha = response.json().get('sha')
            print(f"✓ File exists, SHA: {sha[:8]}...")
        elif response.status_code == 404:
            sha = None
            print("ℹ️ File doesn't exist yet, will create new")
        else:
            print(f"❌ Unexpected response getting file: {response.status_code}")
            print(f"Response: {response.text}")
            st.warning(f"⚠️ GitHub API error: {response.status_code}")
            return False
        
        # Prepare the update
        content_base64 = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": commit_message,
            "content": content_base64,
            "branch": "main"
        }
        
        if sha:
            data["sha"] = sha
        
        # Commit the file
        print(f"📤 Committing to GitHub...")
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            #print(f"✅ Successfully committed {file_path} to GitHub!")
            #st.toast(f"✅ Saved to GitHub!", icon="💾")
            return True
        else:
            error_msg = response.json().get('message', response.text) if response.text else "Unknown error"
            #print(f"❌ Failed to commit: {response.status_code}")
            print(f"Error details: {error_msg}")
            #st.error(f"Failed to save to GitHub: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Error committing to GitHub: {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Error saving to GitHub: {str(e)}")
        return False

def load_books(filepath='data/books.json'):
    '''Load books from JSON file'''
    ensure_data_directory()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📚 Loaded {len(data)} books from {filepath}")
                return data
        except Exception as e:
            print(f"Error loading books: {e}")
            return []
    print(f"ℹ️ No books file found, starting fresh")
    return []

def save_books(books, filepath='data/books.json', auto_commit=True):
    '''Save books to JSON file and optionally commit to GitHub'''
    ensure_data_directory()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(books)} books to local file")
        
        if auto_commit:
            success = commit_to_github(filepath, f"Update books - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            if not success:
                print("⚠️ Failed to commit to GitHub, but saved locally")
    except Exception as e:
        print(f"Error saving books: {e}")
        st.error(f"Error saving books: {e}")

def load_votes(filepath='data/votes.json'):
    '''Load votes from JSON file'''
    ensure_data_directory()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"🗳️ Loaded {len(data)} votes from {filepath}")
                return data
        except Exception as e:
            print(f"Error loading votes: {e}")
            return []
    print(f"ℹ️ No votes file found, starting fresh")
    return []

def save_votes(votes, filepath='data/votes.json', auto_commit=True):
    '''Save votes to JSON file and optionally commit to GitHub'''
    ensure_data_directory()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(votes, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(votes)} votes to local file")
        
        if auto_commit:
            success = commit_to_github(filepath, f"Update votes - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            if not success:
                print("⚠️ Failed to commit to GitHub, but saved locally")
    except Exception as e:
        print(f"Error saving votes: {e}")
        st.error(f"Error saving votes: {e}")

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