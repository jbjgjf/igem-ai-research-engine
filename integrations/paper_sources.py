import arxiv
import time
from typing import List, Dict

# Global client with conservative settings to avoid 429 errors
# delay_seconds=3.0 and num_retries=5 are more robust than defaults.
client = arxiv.Client(
    delay_seconds=3.0,
    num_retries=5
)

def fetch_recent_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fetch recent papers from arXiv based on a query with retry logic.
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers = []
    try:
        # Use the configured client to execute the search
        results_gen = client.results(search)
        
        for result in results_gen:
            if len(papers) >= max_results:
                break
                
            papers.append({
                "title": result.title,
                "abstract": result.summary,
                "authors": [author.name for author in result.authors],
                "published_date": result.published.strftime("%Y-%m-%d")
            })
            
    except arxiv.HTTPError as e:
        if e.status == 429:
            print(f"Error: arXiv API rate limit (429) hit. Please wait before retrying. Details: {e}")
        else:
            print(f"Error: arXiv API HTTP error: {e}")
    except Exception as e:
        print(f"Error: An unexpected error occurred while fetching papers: {e}")
    
    return papers
