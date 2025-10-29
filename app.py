import streamlit as st
import pandas as pd
import json
import os

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from utils.data_manager import (
    load_books, save_books, load_votes, save_votes,
    add_book, book_exists, add_vote, has_voted,
    calculate_scores, export_all_data, import_data
)
from config.settings import (
    APP_TITLE, MAX_VOTES_PER_PERSON, TOTAL_POINTS, TOP_BOOKS_TO_DISPLAY
)

# ==================== APP CONFIG ====================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

USER_LIST = ["Gab", "Nonna", "Phil", "Silvia", "Kathy", "Val"]

# ==================== LOGIN ====================
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.current_user:
    st.title("👋 Welcome to our Book Club Website!")
    st.info("Please select your name to continue:")
    user = st.selectbox("Your Name", USER_LIST, index=None, placeholder="Select your name")

    if st.button("Continue"):
        if user:
            st.session_state.current_user = user
            st.rerun()
        else:
            st.warning("⚠️ Please select your name before continuing.")
    st.stop()
else:
    st.sidebar.success(f"Logged in as: **{st.session_state.current_user}**")
    if st.sidebar.button("🔄 Switch User"):
        st.session_state.current_user = None
        st.rerun()

# ==================== CUSTOM CSS ====================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .book-container {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== DATA LOADING ====================
if 'books' not in st.session_state:
    st.session_state.books = load_books()
if 'votes' not in st.session_state:
    st.session_state.votes = load_votes()

def auto_save():
    save_books(st.session_state.books)
    save_votes(st.session_state.votes)

is_admin = st.session_state.current_user == "Phil"

# ==================== NAVIGATION ====================
if is_admin:
    page = st.sidebar.radio("📍 Navigation", ["Submit Books", "View Books", "Time to Vote!", "Results", "Scraper","🔧 Debug"])
else:
    page = st.sidebar.radio("📍 Navigation", ["Submit Books", "View Books"])
    #st.sidebar.info("📌 You are on the Submit Books page")

# ==================== PAGE 1: SUBMIT BOOKS ====================
if page == "Submit Books":
    user = st.session_state.current_user
    st.markdown(f'<p class="main-header">📚 {user}, Submit Your Book Choice! </p>', unsafe_allow_html=True)

    user_books = [b for b in st.session_state.books if b["submitter"] == user]
    can_submit = len(user_books) < 5

    if not can_submit:
        st.warning("⚠️ You have reached the maximum of 5 submissions. If you want to change your choices, click on the delete button below the removed book.")

    with st.form("book_submission"):
        col1, col2 = st.columns(2)
        with col1:
            book_title = st.text_input("Book Title *", placeholder="e.g., The Great Gatsby")
        with col2:
            author = st.text_input("Author *", placeholder="e.g., F. Scott Fitzgerald")

        submitted = st.form_submit_button("📖 Submit Book", use_container_width=True)

        if submitted:
            if not can_submit:
                st.error("❌ Submission limit reached.")
            elif book_title and author:
                if book_exists(st.session_state.books, book_title, author):
                    st.warning("⚠️ This book has already been submitted! Choose another one.")
                else:
                    # Add basic entry only (no API calls)
                    book_entry = add_book(st.session_state.books, book_title, author, user)
                    st.success(f"✅ '{book_title}' by {author} has been added!")
                    auto_save()
                    st.rerun()
            else:
                st.error("❌ Please fill in all required fields")

    st.divider()

    # ==================== DISPLAY BOOKS ====================
    if st.session_state.books:
        st.subheader(f"📚 Submitted Books")

        if 'selected_book' not in st.session_state:
            st.session_state.selected_book = {}

        for row_start in range(0, len(st.session_state.books), 3):
            cols = st.columns(3)
            for col_idx, col in enumerate(cols):
                book_idx = row_start + col_idx
                if book_idx >= len(st.session_state.books):
                    continue
                book = st.session_state.books[book_idx]
                is_selected = st.session_state.selected_book.get(book_idx, False)

                with col:
                    cover_path = f"covers/{book['title'].replace(' ', '_')}.jpg"
                    has_cover = os.path.exists(cover_path)

                    if has_cover:
                        st.image(cover_path, use_container_width=True)
                    else:
                        st.markdown(f"""
                                <div style="
                                    background-color: white;
                                    border: 1px solid #ddd;
                                    padding: 40px 20px;
                                    text-align: center;
                                    min-height: 300px;
                                ">
                                    <p style="font-weight: bold;">{book['title']}</p>
                                    <p style="color: #666;">{book['author']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                    if user == book["submitter"] or is_admin:
                        if st.button("🗑️ Delete", key=f"delete_{book_idx}", use_container_width=True):
                            st.session_state.books.pop(book_idx)
                            auto_save()
                            st.rerun()
    else:
        st.info("👋 No books submitted yet.")

# ==================== PAGE 2: View Books ====================
elif page == "View Books":
    user = st.session_state.current_user
    
    st.markdown('<p class="main-header">📖 Get to know the submitted books!</p>', unsafe_allow_html=True)
    
    if not st.session_state.books:
        st.warning("📚 No books have been submitted yet. Please go to 'Submit Books' page first.")
    else:
        # Display all books with details
        st.header("📚 Submitted Books")
        
        for idx, book in enumerate(st.session_state.books):
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # Check for cover image in covers folder
                    cover_path = f"covers/{book['title'].replace(' ', '_')}.jpg"
                    if os.path.exists(cover_path):
                        st.image(cover_path, use_container_width=True)
                    else:
                        # Placeholder if no cover
                        st.markdown(f"""
                            <div style="
                                background-color: white;
                                border: 1px solid #ddd;
                                padding: 40px 20px;
                                text-align: center;
                                min-height: 400px;
                                display: flex;
                                flex-direction: column;
                                justify-content: center;
                            ">
                                <p style="color: black; font-size: 1.2rem; font-weight: bold; margin-bottom: 10px;">
                                    {book['title']}
                                </p>
                                <p style="color: #666; font-size: 1rem;">
                                    {book['author']}
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.subheader(f"{book['title']}")
                    st.write(f"**Author:** {book['author']}")
                    st.write(f"**Year:** {book.get('year', 'N/A')}")
                    st.write(f"**Genre:** {book.get('genres', 'N/A')}")
                    st.write(f"**Pages:** {book.get('pages', 'N/A')}")
                    st.write(f"**Summary:** {book.get('summary', 'No summary available')}")
                
                st.divider()

# ==================== PAGE 2: View Books ==================== 
elif page == "Time to Vote!": 
    if not is_admin:
        st.error("⛔ Access Denied: This page is only available to Phil.")
        st.stop()
    
    st.markdown('<p class="main-header">🗳️ Time to Vote!</p>', unsafe_allow_html=True) 

    # Voting Section
    st.header("🗳️ Cast Your Vote")
    st.info(f"💡 Select your top {MAX_VOTES_PER_PERSON} books and distribute {TOTAL_POINTS} points among them. Give more points to your favorites!")
        
    with st.form("voting_form"):
        voter_name = st.text_input("Your Name *", placeholder="Enter your name")
            
    st.write(f"**Select {MAX_VOTES_PER_PERSON} books and allocate {TOTAL_POINTS} points total**")
            
    available_books = [(i, f"{book['title']} by {book['author']}") 
                             for i, book in enumerate(st.session_state.books)]
            
    votes = []
    points = []
            
    for i in range(MAX_VOTES_PER_PERSON):
            col1, col2 = st.columns([3, 1])
                
            with col1:
                filtered_books = [b for b in available_books 
                                    if b[0] not in votes]
                    
                if filtered_books:
                        selected = st.selectbox(
                            f"Choice {i+1} *",
                            options=[b[0] for b in filtered_books],
                            format_func=lambda x: next(b[1] for b in filtered_books if b[0] == x),
                            key=f"book_{i}"
                        )
                        votes.append(selected)
                    
                with col2:
                    point = st.number_input(
                        f"Points *",
                        min_value=0,
                        max_value=TOTAL_POINTS,
                        value=0,
                        key=f"points_{i}",
                        help=f"Allocate points (total must equal {TOTAL_POINTS})"
                    )
                    points.append(point)
            
            # Show current point total
            current_total = sum(points)
            if current_total == TOTAL_POINTS:
                st.success(f"✅ Point allocation: {current_total}/{TOTAL_POINTS}")
            else:
                st.warning(f"⚠️ Point allocation: {current_total}/{TOTAL_POINTS}")
            
            submitted_vote = st.form_submit_button("🗳️ Submit Vote", use_container_width=True)
            
            if submitted_vote:
                if not voter_name:
                    st.error("❌ Please enter your name")
                elif sum(points) != TOTAL_POINTS:
                    st.error(f"❌ Points must total {TOTAL_POINTS}. Current total: {sum(points)}")
                elif len(set(votes)) != MAX_VOTES_PER_PERSON:
                    st.error(f"❌ Please select {MAX_VOTES_PER_PERSON} different books")
                elif 0 in points:
                    st.error("❌ All choices must have at least 1 point")
                else:
                    if has_voted(st.session_state.votes, voter_name):
                        st.warning("⚠️ You have already voted! Contact admin to reset your vote.")
                    else:
                        user_submission = next((i for i, b in enumerate(st.session_state.books) 
                                              if b['submitter'].lower() == voter_name.lower()), None)
                        
                        if user_submission in votes:
                            st.error("❌ You cannot vote for your own submission!")
                        else:
                            add_vote(st.session_state.votes, voter_name, list(zip(votes, points)))
                            auto_save()
                            st.success("✅ Your vote has been recorded!")
                            st.balloons()
                            st.rerun()

# ==================== PAGE 3: Time to Vote! ==================== 
elif page == "Time to Vote!": 
    if not is_admin:
        st.error("⛔ Access Denied: This page is only available to Phil.")
        st.stop()
    
    st.markdown('<p class="main-header">🗳️ Time to Vote!</p>', unsafe_allow_html=True) 

    if not st.session_state.books:
        st.warning("📚 No books have been submitted yet.")
    else:
        # Voting Section
        st.header("🗳️ Cast Your Vote")
        st.info(f"💡 Select your top {MAX_VOTES_PER_PERSON} books and distribute {TOTAL_POINTS} points among them. Give more points to your favorites!")
            
        with st.form("voting_form"):
            voter_name = st.text_input("Your Name *", placeholder="Enter your name")
                
            st.write(f"**Select {MAX_VOTES_PER_PERSON} books and allocate {TOTAL_POINTS} points total**")
                
            available_books = [(i, f"{book['title']} by {book['author']}") 
                                for i, book in enumerate(st.session_state.books)]
                
            votes = []
            points = []
                
            for i in range(MAX_VOTES_PER_PERSON):
                col1, col2 = st.columns([3, 1])
                    
                with col1:
                    filtered_books = [b for b in available_books 
                                        if b[0] not in votes]
                        
                    if filtered_books:
                        selected = st.selectbox(
                            f"Choice {i+1} *",
                            options=[b[0] for b in filtered_books],
                            format_func=lambda x: next(b[1] for b in filtered_books if b[0] == x),
                            key=f"book_{i}"
                        )
                        votes.append(selected)
                        
                with col2:
                    point = st.number_input(
                        f"Points *",
                        min_value=0,
                        max_value=TOTAL_POINTS,
                        value=0,
                        key=f"points_{i}",
                        help=f"Allocate points (total must equal {TOTAL_POINTS})"
                    )
                    points.append(point)
                
            # Show current point total
            current_total = sum(points)
            if current_total == TOTAL_POINTS:
                st.success(f"✅ Point allocation: {current_total}/{TOTAL_POINTS}")
            else:
                st.warning(f"⚠️ Point allocation: {current_total}/{TOTAL_POINTS}")
                
            submitted_vote = st.form_submit_button("🗳️ Submit Vote", use_container_width=True)
                
            if submitted_vote:
                if not voter_name:
                    st.error("❌ Please enter your name")
                elif sum(points) != TOTAL_POINTS:
                    st.error(f"❌ Points must total {TOTAL_POINTS}. Current total: {sum(points)}")
                elif len(set(votes)) != MAX_VOTES_PER_PERSON:
                    st.error(f"❌ Please select {MAX_VOTES_PER_PERSON} different books")
                elif 0 in points:
                    st.error("❌ All choices must have at least 1 point")
                else:
                    if has_voted(st.session_state.votes, voter_name):
                        st.warning("⚠️ You have already voted! Contact admin to reset your vote.")
                    else:
                        user_submission = next((i for i, b in enumerate(st.session_state.books) 
                                                if b['submitter'].lower() == voter_name.lower()), None)
                            
                        if user_submission in votes:
                            st.error("❌ You cannot vote for your own submission!")
                        else:
                            add_vote(st.session_state.votes, voter_name, list(zip(votes, points)))
                            auto_save()
                            st.success("✅ Your vote has been recorded!")
                            st.balloons()
                            st.rerun()

# ==================== PAGE: Scraper (Phil Only) ====================
elif page == "Scraper":
    if not is_admin:
        st.error("⛔ Access Denied: This page is only available to Phil.")
        st.stop()
    
    st.markdown('<p class="main-header">🔍 Goodreads Shelf Scraper</p>', unsafe_allow_html=True)
    
    st.info("💡 Add all submitted books to a Goodreads shelf, then scrape the data here to auto-populate book details!")
    
    # Instructions
    with st.expander("📖 How to use this scraper"):
        st.markdown("""
        ### Steps:
        1. Go to [Goodreads](https://www.goodreads.com) and log in
        2. Go to "My Books" → Select or create a shelf (e.g., "bookclub2026nominees")
        3. Add all submitted books to that shelf
        4. Copy the shelf URL (it looks like: `https://www.goodreads.com/review/list/YOUR_ID?shelf=SHELF_NAME`)
        5. Paste it below and click "Scrape Shelf"
        6. Review the data and click "Update Books" to apply
        
        ### What this scrapes:
        - ✅ Title & Author
        - ✅ Cover image (high resolution)
        - ✅ Publication year
        - ✅ Number of pages
        - ✅ Average rating
        - ✅ Summary & genres (from individual book pages)
        """)
    
    st.divider()
    
    # Scraper UI
    st.header("🔍 Scrape Goodreads Shelf")
    
    shelf_url = st.text_input(
        "Goodreads Shelf URL *",
        placeholder="https://www.goodreads.com/review/list/121203593-philippe?shelf=bookclub2026nominees",
        help="Get this from your Goodreads shelf page"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        scrape_details = st.checkbox("Include summaries & genres", value=True, 
                                     help="Takes longer (~1 sec per book)")
    
    with col2:
        if st.button("🔍 Scrape Shelf", use_container_width=True, type="primary"):
            if not shelf_url:
                st.error("❌ Please enter a shelf URL")
            else:
                try:
                    from utils.goodreads_scraper import scrape_goodreads_shelf, enrich_books_with_details
                    
                    with st.spinner("🔍 Scraping Goodreads shelf..."):
                        books_data = scrape_goodreads_shelf(shelf_url)
                        
                        if books_data:
                            st.success(f"✅ Found {len(books_data)} books on shelf!")
                            
                            if scrape_details:
                                with st.spinner(f"📚 Getting detailed info for {len(books_data)} books... (this may take a minute)"):
                                    books_data = enrich_books_with_details(books_data)
                                st.success("✅ Enriched with summaries and genres!")
                            
                            # Store in session state for review
                            st.session_state.scraped_books = books_data
                            st.rerun()
                        else:
                            st.error("❌ No books found. Check your shelf URL.")
                
                except ImportError:
                    st.error("❌ Scraper module not found. Make sure `utils/goodreads_scraper.py` exists.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.code(str(e))
    
    st.divider()
    
    # Display scraped data if available
    if 'scraped_books' in st.session_state and st.session_state.scraped_books:
        scraped_books = st.session_state.scraped_books
        
        st.header(f"📚 Scraped Data ({len(scraped_books)} books)")
        
        # Show preview
        for i, book in enumerate(scraped_books):
            with st.expander(f"📖 {book.get('title', 'Unknown')} by {book.get('author', 'Unknown')}"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if book.get('image_url'):
                        st.image(book['image_url'], width=150)
                    else:
                        st.write("📘 No image")
                
                with col2:
                    st.write(f"**Title:** {book.get('title', 'N/A')}")
                    st.write(f"**Author:** {book.get('author', 'N/A')}")
                    st.write(f"**Year:** {book.get('year', 'N/A')}")
                    st.write(f"**Pages:** {book.get('pages', 'N/A')}")
                    st.write(f"**Rating:** {book.get('rating', 'N/A')} ⭐")
                    st.write(f"**Genres:** {book.get('genres', 'N/A')}")
                    st.write(f"**Summary:** {book.get('summary', 'No summary available')[:200]}...")
        
        st.divider()
        
        # Match with existing books
        st.header("🔗 Match with Submitted Books")
        
        st.info("Match scraped data with books already submitted to the book club")
        
        # Create matching interface
        matched_books = []
        
        for scraped_book in scraped_books:
            st.subheader(f"📖 {scraped_book.get('title')} by {scraped_book.get('author')}")
            
            # Find potential matches in existing books
            potential_matches = []
            for idx, existing_book in enumerate(st.session_state.books):
                # Simple matching by title similarity
                if (scraped_book.get('title', '').lower() in existing_book['title'].lower() or
                    existing_book['title'].lower() in scraped_book.get('title', '').lower()):
                    potential_matches.append((idx, existing_book))
            
            if potential_matches:
                match_options = ["Don't update"] + [f"{b['title']} by {b['author']} (submitted by {b['submitter']})" 
                                                     for _, b in potential_matches]
                
                selected = st.selectbox(
                    "Match with existing book:",
                    options=range(len(match_options)),
                    format_func=lambda x: match_options[x],
                    key=f"match_{scraped_book.get('title')}"
                )
                
                if selected > 0:
                    book_idx = potential_matches[selected - 1][0]
                    matched_books.append((book_idx, scraped_book))
            else:
                st.warning("⚠️ No matching book found in submitted books")
            
            st.divider()
        
        # Apply updates
        if matched_books:
            st.header("💾 Apply Updates")
            
            st.write(f"**Ready to update {len(matched_books)} books**")
            
            if st.button("✅ Update Books with Scraped Data", type="primary", use_container_width=True):
                for book_idx, scraped_data in matched_books:
                    # Update existing book with scraped data
                    st.session_state.books[book_idx].update({
                        'year': scraped_data.get('year', 'N/A'),
                        'pages': scraped_data.get('pages', 'N/A'),
                        'genres': scraped_data.get('genres', 'N/A'),
                        'summary': scraped_data.get('summary', 'No summary available'),
                        'image_url': scraped_data.get('image_url'),
                        'rating': scraped_data.get('rating'),
                        'url': scraped_data.get('url')
                    })
                
                # Save to GitHub
                auto_save()
                
                # Clear scraped data
                del st.session_state.scraped_books
                
                st.success(f"✅ Successfully updated {len(matched_books)} books!")
                st.balloons()
                st.rerun()
        
        # Download as JSON
        st.divider()
        st.header("📥 Download Scraped Data")
        
        import json
        json_data = json.dumps(scraped_books, indent=2, ensure_ascii=False)
        
        st.download_button(
            "⬇️ Download as JSON",
            data=json_data,
            file_name="goodreads_scraped_books.json",
            mime="application/json",
            use_container_width=True
        )
        
        if st.button("🗑️ Clear Scraped Data", use_container_width=True):
            del st.session_state.scraped_books
            st.rerun()

# ==================== PAGE 4: Debug (Phil Only) ====================
elif page == "🔧 Debug":
    if not is_admin:
        st.error("⛔ Access Denied")
        st.stop()
    
    st.title("🔧 Debug & Diagnostics")
    
    st.header("1️⃣ GitHub Secrets Check")
    if "github" in st.secrets:
        st.success("✅ GitHub secrets are configured!")
        st.write(f"**Username:** {st.secrets['github']['username']}")
        st.write(f"**Repo:** {st.secrets['github']['repo']}")
        st.write(f"**Token:** `{st.secrets['github']['token'][:10]}...` (hidden)")
    else:
        st.error("❌ GitHub secrets NOT found!")
        st.info("Go to Streamlit Cloud → App Settings → Secrets and add your GitHub credentials")
    
    st.divider()
    
    st.header("2️⃣ Test GitHub Connection")
    if st.button("🧪 Test GitHub API Connection"):
        try:
            import requests
            token = st.secrets["github"]["token"]
            username = st.secrets["github"]["username"]
            repo = st.secrets["github"]["repo"]
            
            with st.spinner("Testing connection..."):
                # Test API access
                api_url = f"https://api.github.com/repos/{username}/{repo}"
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                response = requests.get(api_url, headers=headers)
                
                if response.status_code == 200:
                    st.success("✅ Successfully connected to GitHub!")
                    repo_data = response.json()
                    st.write(f"**Repo Name:** {repo_data['name']}")
                    st.write(f"**Full Name:** {repo_data['full_name']}")
                    st.write(f"**Default Branch:** {repo_data['default_branch']}")
                else:
                    st.error(f"❌ Connection failed: {response.status_code}")
                    st.code(response.text)
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    st.divider()
    
    st.header("3️⃣ Current Data")
    st.write(f"**Books loaded:** {len(st.session_state.books)}")
    st.write(f"**Votes loaded:** {len(st.session_state.votes)}")
    
    if st.session_state.books:
        st.subheader("Books in Memory:")
        st.json(st.session_state.books)
    
    st.divider()
    
    st.header("4️⃣ Manual GitHub Push Test")
    if st.button("🚀 Manually Push books.json to GitHub"):
        from utils.data_manager import commit_to_github
        success = commit_to_github('data/books.json', 'Manual test commit from debug page')
        if success:
            st.success("✅ Successfully pushed to GitHub!")
        else:
            st.error("❌ Failed to push to GitHub - check logs")
    
    st.divider()
    
    st.header("5️⃣ Check GitHub Files")
    if st.button("🔍 Check if data files exist in GitHub"):
        try:
            token = st.secrets["github"]["token"]
            username = st.secrets["github"]["username"]
            repo = st.secrets["github"]["repo"]
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            for filename in ['data/books.json', 'data/votes.json']:
                api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{filename}"
                response = requests.get(api_url, headers=headers)
                
                if response.status_code == 200:
                    st.success(f"✅ `{filename}` exists in GitHub")
                    data = response.json()
                    st.write(f"  - Size: {data['size']} bytes")
                    st.write(f"  - SHA: {data['sha'][:8]}...")
                elif response.status_code == 404:
                    st.warning(f"⚠️ `{filename}` NOT found in GitHub")
                else:
                    st.error(f"❌ Error checking `{filename}`: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")

# ==================== SIDEBAR: Data Management ====================
with st.sidebar:
    st.divider()
    st.header("Submissions")
    
    # Stats
    st.metric("📚 Books", len(st.session_state.books))
    #st.metric("🗳️ Votes", len(st.session_state.votes))
    
    st.divider()
    
    # Admin tools - only for Phil
    if is_admin:
        st.subheader("🔧 Admin Tools")
        
        # Export
        if st.button("📥 Export Data", use_container_width=True):
            export_data = export_all_data(st.session_state.books, st.session_state.votes)
            st.download_button(
                "⬇️ Download JSON",
                data=export_data,
                file_name=f"bookclub_backup.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Import
        uploaded_file = st.file_uploader("📤 Import Data", type=['json'])
        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode('utf-8')
                books, votes = import_data(content)
                if books is not None:
                    if st.button("✅ Confirm Import", use_container_width=True):
                        st.session_state.books = books
                        st.session_state.votes = votes
                        auto_save()
                        st.success("Data imported successfully!")
                        st.rerun()
                else:
                    st.error("Invalid file format")
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        # Reset
        if st.button("🗑️ Clear All Data", use_container_width=True):
            if st.checkbox("I understand this will delete everything"):
                st.session_state.books = []
                st.session_state.votes = []
                auto_save()
                st.success("All data cleared!")
                st.rerun()
    
    st.divider()
    st.caption("Made with ❤️ for book lovers")