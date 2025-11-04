# 📚 Book Club Voting System

A Streamlit application for managing book club selections and voting.

## Features
- Submit book nominations with automatic Goodreads data fetching
- View all nominated books with covers, summaries, and details
- Vote for your top 6 books with point allocation (100 points total)
- View results and rankings

## Local Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd bookclub_streamlit

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Deployment to Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository, branch (main), and file path (app.py)
6. Click "Deploy"!

Your app will be live at: `https://[your-username]-bookclub.streamlit.app`

## Usage

1. **Submit Books**: Navigate to the first page and submit book nominations
2. **Vote**: View all books and cast your vote with point allocation
3. **Results**: See the top 6 books selected by the group

## Data Persistence

Data is stored using Streamlit's session state and saved to JSON files. 
For cloud deployment, data persists across sessions but resets on app restarts.
Use the Export feature to backup your data regularly!

## Configuration

Edit `config/settings.py` to customize:
- Number of votes per person
- Total points to allocate
- Number of top books to display