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
    page = st.sidebar.radio("📍 Navigation", ["Submit Books", "Time to Vote!!"])
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
    user_books = [book for book in st.session_state.books if book["submitter"] == user]

    if user_books: 
        st.subheader(f"📚 Your Submitted Books")

        if 'selected_book' not in st.session_state:
            st.session_state.selected_book = {}

        for row_start in range(0, len(user_books), 3):
            cols = st.columns(3)
            for col_idx, col in enumerate(cols):
                book_idx = row_start + col_idx
                if book_idx >= len(user_books):
                    continue
                book = user_books[book_idx]
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

        sorted_books = sorted(
            st.session_state.books, 
            key=lambda book: (book["author"].split(" ",1)[1]))
        
        for idx, book in enumerate(sorted_books):
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
elif page == "Results":
    st.markdown('<p class="main-header">🏆 Final Results</p>', unsafe_allow_html=True)

    if not st.session_state.books:
        st.warning("📚 No books have been submitted yet.")
        st.stop()

    if not st.session_state.votes:
        st.warning("🗳️ No votes have been submitted yet.")
        st.stop()

    books = st.session_state.books
    votes = st.session_state.votes

    book_scores = {book["title"]: 0 for book in books}
    book_voters = {book["title"]: [] for book in books}

    for vote_entry in votes:
        voter_name = vote_entry["voter"]
        for book_index, points in vote_entry["votes"]:
            if 0 <= book_index < len(books):
                book = books[book_index]
                book_scores[book["title"]] += points
                book_voters[book["title"]].append({"voter": voter_name, "points": points})

    for book in books:
        book["total_points"] = book_scores.get(book["title"], 0)
        book["voters"] = book_voters.get(book["title"], [])

    voted_books = [b for b in books if b["total_points"] > 0]
    unvoted_books = [b for b in books if b["total_points"] == 0]

    ranked_books = sorted(voted_books, key=lambda b: b["total_points"], reverse=True)

    st.header("📊 Results Overview")

    if unvoted_books:
        with st.expander("Received No Votes"):
            cols = st.columns(4)
            for i, book in enumerate(unvoted_books):
                with cols[i % 4]:
                    cover_path = f"covers/{book['title'].replace(' ', '_')}.jpg"
                    if os.path.exists(cover_path):
                        st.image(cover_path, caption=f"{book['title']} — {book['author']}", use_container_width=True)
                    else:
                        st.markdown(f"""
                            <div style="
                                background-color: white;
                                border: 1px solid #ddd;
                                padding: 10px;
                                text-align: center;
                                border-radius: 10px;
                                margin-bottom: 10px;
                            ">
                                <p style="font-weight: bold;">{book['title']}</p>
                                <p style="color: #666;">{book['author']}</p>
                            </div>
                        """, unsafe_allow_html=True)

    for idx, book in enumerate(reversed(ranked_books), start=1):  # lowest first
        rank = len(ranked_books) - idx + 1  # actual rank
        is_top6 = rank <= 6

        border_color = "#FFD700" if is_top6 else "#ddd"
        bg_color = "#fff9e6" if is_top6 else "white"

        with st.expander(f"#{rank}"):
            col1, col2 = st.columns([1, 2])

            with col1: 
            #st.markdown(f"""
                #<div style="
                    #border: 3px solid {border_color};
                    #border-radius: 12px;
                    #padding: 20px;
                    #background-color: {bg_color};
                    #margin-bottom: 10px;
                #">
                    #<h3 style="margin-bottom: 5px;">#{rank} – {book['title']}</h3>
                    #<p><b>Author:</b> {book['author']}</p>
                    #<p><b>Submitted by:</b> {book['submitter']}</p>
                    #<p><b>Total Points:</b> {book['total_points']}</p>
            #""", unsafe_allow_html=True)

                cover_path = f"covers/{book['title'].replace(' ', '_')}.jpg"
                #if os.path.exists(cover_path):
                st.image(cover_path, width=200)
                #else:
                    #st.markdown(f"""
                        #<div style="
                            #background-color: white;
                            #border: 1px solid #ddd;
                            #padding: 20px;
                            #text-align: center;
                            #width: 200px;
                            #margin-bottom: 10px;
                        #">
                            #<p style="font-weight: bold;">{book['title']}</p>
                            #<p style="color: #666;">{book['author']}</p>
                        #</div>
                    #""", unsafe_allow_html=True)

            with col2: 
                st.markdown(f"""
                <div style="
                    border: 3px solid {border_color};
                    #border-radius: 12px;
                    padding: 20px;
                    background-color: {bg_color};
                ">
                    <h3 style="margin-bottom: 5px;">#{rank} – {book['title']}</h3>
                    <p><b>Author:</b> {book['author']}</p>
                    <p><b>Submitted by:</b> {book['submitter']}</p>
                    <p><b>Total Points:</b> {book['total_points']}</p>
                    <hr>
            """, unsafe_allow_html=True)

                st.write("### 🗳️ Votes Received:")
                if book["voters"]:
                    for v in sorted(book["voters"], key=lambda x: x["points"], reverse=True):
                        st.write(f"- {v['voter']} gave **{v['points']} points**")
                else:
                    st.write("_No votes yet_")

            st.markdown("</div>", unsafe_allow_html=True)

    # 8️⃣ Fun Stats
    st.divider()
    st.header("🎉 Fun Stats")

    # 🏅 Top Submitter
    submitter_totals = {}
    for book in books:
        submitter_totals[book["submitter"]] = submitter_totals.get(book["submitter"], 0) + book["total_points"]

    top_submitter = max(submitter_totals, key=submitter_totals.get)
    st.write(f"🏅 **Top Submitter:** {top_submitter} — {submitter_totals[top_submitter]} total points received")

    # 🤓 Best Voter — voted for most Top 6 books
    top6_titles = [b["title"] for b in ranked_books[:6]]
    voter_counts = {}

    for vote_entry in votes:
        voter = vote_entry["voter"]
        count_top6 = sum(
            1 for (book_index, _) in vote_entry["votes"]
            if books[book_index]["title"] in top6_titles
        )
        if count_top6 > 0:
            voter_counts[voter] = count_top6

    if voter_counts:
        best_voter = max(voter_counts, key=voter_counts.get)
        st.write(f"🤓 **Best Voter:** {best_voter} — voted for {voter_counts[best_voter]} of the Top 6 books!")
    else:
        st.write("No top-6 votes recorded yet.")

    st.divider()
    st.success("🌟 The Top 6 books (highlighted in gold) are the final selections!")                   

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