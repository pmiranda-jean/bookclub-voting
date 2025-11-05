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

USER_LIST = ["Gab", "Grace", "Phil", "Silvia", "Kathy", "Val"]

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
    page = st.sidebar.radio("📍 Navigation", ["Submit Books", "View Books", "Time to Vote!!", "Results"])
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
        st.subheader(f"📚 Your Submitted Books")

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
    book = [b for b in st.session_state.books if b["submitter"] == user]
    
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
                    st.write(f"**Link:** {book.get('url', 'N/A')}")
                    st.write(f"**Summary:** {book.get('summary', 'No summary available')}")
                
                st.divider()
# ==================== PAGE 3: Time to Vote! ==================== 
elif page == "Time to Vote!!": 
    if not is_admin:
        st.error("⛔ Access Denied: This page is only available to Phil.")
        st.stop()
    
    st.markdown('<p class="main-header">🗳️ Time to Vote!</p>', unsafe_allow_html=True) 

    if not st.session_state.books:
        st.warning("📚 No books have been submitted yet.")
    else:
        # Voting Section
        st.info(f"💡 Distribute {TOTAL_POINTS} points among the books below. Give more points to your favorites! You cannot vote for books you submitted.")
        
        # Get current user's name
        voter_name = st.session_state.current_user
        
        # Check if already voted
        if has_voted(st.session_state.votes, voter_name):
            st.warning("⚠️ You have already voted! Contact Phil if you need to change your vote.")
            st.stop()
        
        # Filter out user's own submissions
        available_books = [
            (idx, book) for idx, book in enumerate(st.session_state.books)
            if book['submitter'] != voter_name
        ]
        
        if not available_books:
            st.error("❌ No books available to vote on (you've submitted all books!)")
            st.stop()
        
        st.divider()
        
        # Display books in 5-column grid
        st.header("📚 Cast Your Votes")
        
        # Use a form to batch all inputs together
        with st.form("voting_grid_form"):
            vote_points = {}
            
            num_cols = 5
            num_books = len(available_books)
            
            for row_start in range(0, num_books, num_cols):
                cols = st.columns(num_cols)
                
                for col_idx, col in enumerate(cols):
                    book_idx_in_list = row_start + col_idx
                    
                    if book_idx_in_list < num_books:
                        original_idx, book = available_books[book_idx_in_list]
                        
                        with col:
                            # Display cover
                            cover_path = f"covers/{book['title'].replace(' ', '_')}.jpg"
                            if os.path.exists(cover_path):
                                st.image(cover_path, use_column_width=True)
                            else:
                                # Placeholder
                                st.markdown(f"""
                                    <div style="
                                        background-color: white;
                                        border: 1px solid #ddd;
                                        padding: 30px 10px;
                                        text-align: center;
                                        min-height: 250px;
                                        display: flex;
                                        flex-direction: column;
                                        justify-content: center;
                                    ">
                                        <p style="font-weight: bold; font-size: 0.9rem; margin: 0;">
                                            {book['title']}
                                        </p>
                                        <p style="color: #666; font-size: 0.8rem; margin-top: 5px;">
                                            {book['author']}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            # Title and author
                            st.markdown(f"**{book['title']}**")
                            st.caption(f"by {book['author']}")
                            
                            # Point dropdown (0-50)
                            points = st.selectbox(
                                "Points",
                                options=list(range(0, 51)),
                                index=0,
                                key=f"vote_select_{original_idx}",
                                label_visibility="collapsed"
                            )
                            
                            vote_points[original_idx] = points
            
            st.divider()
            
            # Submit button
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                submitted = st.form_submit_button("🗳️ Submit Vote", use_container_width=True, type="primary")
            
            if submitted:
                # Calculate total
                total_allocated = sum(vote_points.values())
                
                # Display current allocation
                st.write(f"**Points allocated:** {total_allocated} / {TOTAL_POINTS}")
                
                if total_allocated != TOTAL_POINTS:
                    st.error(f"❌ You must allocate exactly {TOTAL_POINTS} points. Currently allocated: {total_allocated}")
                else:
                    # Get books with points > 0
                    votes_to_submit = [
                        (idx, points) for idx, points in vote_points.items()
                        if points > 0
                    ]
                    
                    if not votes_to_submit:
                        st.error("❌ You must vote for at least one book!")
                    else:
                        # Save vote
                        add_vote(st.session_state.votes, voter_name, votes_to_submit)
                        auto_save()
                        
                        st.success("✅ Your vote has been recorded!")
                        st.balloons()
                        st.rerun()

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