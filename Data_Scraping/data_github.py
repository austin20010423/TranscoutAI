import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


# The GitHub API endpoint for searching repositories
API_URL = "https://api.github.com/search/repositories"


def check_token():
    """Checks if the token has been set."""
    if not config.GITHUB_TOKEN or "PASTE_YOUR" in config.GITHUB_TOKEN:
        print("[ERROR] You forgot to paste your GITHUB_TOKEN into the script.")
        print("        Please get a token from https://github.com/settings/tokens")
        sys.exit(1) # Exit the script

def fetch_trending_repos():
    """
    Fetches trending AI repositories from GitHub.
    """
    print(f"[INFO] Searching GitHub for: '{config.SEARCH_QUERY}'...")

    # Set up the query parameters
    params = {
        "q": config.SEARCH_QUERY,
        "sort": config.SORT_BY,
        "order": config.ORDER,
        "per_page": 10  # the top 10 for this demo
    }


    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        response = requests.get(API_URL, headers=headers, params=params)

        # Raise an error if the request failed (e.g., 401 Unauthorized)
        response.raise_for_status()

        data = response.json()

        if "items" not in data:
            print("[WARN] 'items' key not in response. No results?")
            return []

        return data["items"]

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 401:
            print("[ERROR] HTTP 401: Unauthorized. Is your GITHUB_TOKEN correct?")
        else:
            print(f"[ERROR] HTTP error occurred: {http_err}")
        return []
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return []

def github_main_ingestion():
    """
    Main function to run the GitHub ingestion.
    """
    print("--- TrendScout AI: Starting GitHub Ingestion ---")

    # Make sure the user added their token
    check_token()

    repos = fetch_trending_repos()

    if not repos:
        print("[INFO] No repositories found or an error occurred.")
        return

    print(f"\n--- Ingestion Complete: Found {len(repos)} relevant repositories ---")



    print("\n--- Top Trending Repos ---")

    repoInJsonList = []

    for i, repo in enumerate(repos):
        '''
        print(f"\nRank {i+1}:")
        print(f"  Name: {repo['full_name']}")
        print(f"  Stars: {repo['stargazers_count']} ⭐")
        print(f"  Desc: {repo['description']}")
        print(f"  URL: {repo['html_url']}")
        '''

        # orginize data into json format
        repoInJson = {
            "name": repo['full_name'],
            "stars": repo['stargazers_count'],
            "description": repo['description'],
            "url": repo['html_url']
        }

        repoInJsonList.append(repoInJson)

    return repoInJsonList

if __name__ == "__main__":
    github_main_ingestion()
