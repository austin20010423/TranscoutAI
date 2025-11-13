from Data_Scraping import data_RSS, data_github


class data_organizer:

    def __init__(self):
        pass

    def data_orginize_RSS():
        # Fetch RSS article data
        articles = data_RSS.techcrunch_main_ingestion_loop()
        print(f"\n--- Ingestion Complete: Total {len(articles)} articles fetched ---")
        
        return articles

    def data_orginize_github():

        # Fetch GitHub repository data
        repos = data_github.github_main_ingestion()
        print(f"\n--- Ingestion Complete: Found {len(repos)} relevant repositories ---")
        
        return repos
