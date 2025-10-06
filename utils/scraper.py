import requests
import streamlit as st
import re
from config.settings import REQUEST_TIMEOUT

import requests
import streamlit as st
import re
from config.settings import REQUEST_TIMEOUT

def fetch_book_data_wikipedia(book_title, author):
    """Fetch book information from Wikipedia API."""
    try:
        base_url = "https://en.wikipedia.org/w/api.php"
        query = f"{book_title} {author}"

        # Step 1: Search for the most relevant page
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        search_response = requests.get(base_url, params=search_params, timeout=REQUEST_TIMEOUT)
        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get("query", {}).get("search"):
            return None

        page_title = search_data["query"]["search"][0]["title"]

        # Step 2: Get page summary + image (this endpoint is simpler and more consistent)
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
        summary_response = requests.get(summary_url, timeout=REQUEST_TIMEOUT)
        summary_response.raise_for_status()
        summary_data = summary_response.json()

        book_info = {
            "api_title": summary_data.get("title", book_title),
            "api_authors": author,
            "summary": summary_data.get("extract", "No summary available"),
            "image_url": summary_data.get("thumbnail", {}).get("source"),
            "pages": "N/A",
            "genres": "N/A",
            "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }

        return book_info

    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch data from Wikipedia: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"Error processing Wikipedia book data: {str(e)}")
        return None

def get_default_book_data():
    """Return default book data when API fetch fails."""
    return {
        "pages": "N/A",
        "image_url": None,
        "genres": "N/A",
        "summary": "No summary available",
        "url": None,
        "publisher": "N/A",
        "published_date": "N/A"
    }
