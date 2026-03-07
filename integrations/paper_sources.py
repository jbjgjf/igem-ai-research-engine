import arxiv
from typing import List, Dict

def fetch_recent_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fetch recent papers from arXiv based on a query.
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers = []
    for result in search.results():
        papers.append({
            "title": result.title,
            "abstract": result.summary,
            "authors": [author.name for author in result.authors],
            "published_date": result.published.strftime("%Y-%m-%d")
        })
    
    return papers
