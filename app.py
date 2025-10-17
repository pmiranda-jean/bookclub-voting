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
    page = st.sidebar.radio("📍 Navigation", ["Submit Books", "View Books", "Time to Vote!", "Results", "🔧 Debug"])
else:
    page = "Submit Books"
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


# ==================== PAGE 3: Results (Phil Only) ====================
elif page == "Results":
    if not is_admin:
        st.error("⛔ Access Denied: This page is only available to Phil.")
        st.stop()
    
    st.markdown('<p class="main-header">🏆 Voting Results</p>', unsafe_allow_html=True)
    
    if not st.session_state.votes:
        st.warning("🗳️ No votes have been cast yet.")
    else:
        book_scores = calculate_scores(st.session_state.votes)
        sorted_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Total Books", len(st.session_state.books))
        with col2:
            st.metric("🗳️ Total Votes", len(st.session_state.votes))
        with col3:
            st.metric("👥 Participation", f"{len(st.session_state.votes)}/{len(st.session_state.books)}")
        
        st.divider()
        
        # Display top books
        st.header(f"🏆 Top {TOP_BOOKS_TO_DISPLAY} Books")
        
        for rank, (book_idx, total_points) in enumerate(sorted_books[:TOP_BOOKS_TO_DISPLAY], 1):
            book = st.session_state.books[book_idx]
            
            # Medal emojis for top 3
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
            
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"### {medal}")
                    if book.get('image_url'):
                        st.image(book['image_url'], use_container_width=True)
                
                with col2:
                    st.subheader(f"{book['title']}")
                    st.write(f"**Author:** {book['author']}")
                    st.write(f"**Total Points:** {total_points} 🌟")
                    
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.write(f"📄 **Pages:** {book.get('pages', 'N/A')}")
                    with info_col2:
                        st.write(f"🏷️ **Genre:** {book.get('genres', 'N/A')}")
                    
                    # Show vote breakdown
                    votes_for_book = [(v['voter'], next(p for idx, p in v['votes'] if idx == book_idx)) 
                                     for v in st.session_state.votes 
                                     if book_idx in [idx for idx, p in v['votes']]]
                    
                    with st.expander("👥 See vote breakdown"):
                        for voter, pts in sorted(votes_for_book, key=lambda x: x[1], reverse=True):
                            st.write(f"• **{voter}**: {pts} points")
                
                st.divider()
        
        # Display all results in table
        with st.expander("📊 See complete rankings"):
            df_results = []
            for rank, (book_idx, total_points) in enumerate(sorted_books, 1):
                book = st.session_state.books[book_idx]
                vote_count = len([v for v in st.session_state.votes 
                                 if book_idx in [idx for idx, p in v['votes']]])
                df_results.append({
                    'Rank': rank,
                    'Title': book['title'],
                    'Author': book['author'],
                    'Points': total_points,
                    'Votes': vote_count,
                    'Submitter': book['submitter']
                })
            
            st.dataframe(pd.DataFrame(df_results), use_container_width=True, hide_index=True)

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
    st.metric("🗳️ Votes", len(st.session_state.votes))
    
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