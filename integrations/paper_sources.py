import arxiv
import time
import requests
import re
from typing import List, Dict, Optional
from datetime import datetime
from config import settings

# Global client for arXiv
arxiv_client = arxiv.Client(
    delay_seconds=3.0,
    num_retries=5,
    page_size=10
)

def normalize_paper(data: Dict, source: str) -> Dict:
    """Standardize paper object from different sources."""
    normalized = {
        "source": source,
        "title": data.get("title", "Untitled").strip(),
        "abstract": data.get("abstract") or data.get("summary") or "No abstract available.",
        "authors": data.get("authors", []),
        "published_date": data.get("published_date") or data.get("year"),
        "url": data.get("url") or data.get("venue_url"),
        "external_id": str(data.get("external_id") or data.get("paperId") or ""),
        "doi": data.get("doi"),
        "relevance_score": 0.0
    }
    
    # Handle PubMed specific fields
    if source == "PubMed":
        normalized["external_id"] = data.get("pmid", normalized["external_id"])
        if not normalized["url"] and normalized["external_id"]:
            normalized["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{normalized['external_id']}/"
            
    # Handle Semantic Scholar specific fields
    if source in ["Semantic Scholar", "bioRxiv"]:
        if not normalized["authors"] and data.get("authors"):
            normalized["authors"] = [a.get("name") for a in data.get("authors") if a.get("name")]
        if not normalized["published_date"] and data.get("year"):
            normalized["published_date"] = str(data.get("year"))

    return normalized

def fetch_arxiv_papers(query: str, max_results: int = 5) -> List[Dict]:
    """Fetch from arXiv."""
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    papers = []
    try:
        results_gen = arxiv_client.results(search)
        for result in results_gen:
            papers.append(normalize_paper({
                "title": result.title,
                "summary": result.summary,
                "authors": [author.name for author in result.authors],
                "published_date": result.published.strftime("%Y-%m-%d"),
                "url": result.entry_id,
                "doi": result.doi,
                "external_id": result.get_short_id()
            }, "arXiv"))
    except Exception as e:
        print(f"Error fetching from arXiv: {e}")
    
    return papers

def fetch_pubmed_papers(query: str, max_results: int = 5) -> List[Dict]:
    """Fetch from PubMed using Entrez E-utilities."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    papers = []
    try:
        # Search for IDs
        search_url = f"{base_url}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results
        }
        resp = requests.get(search_url, params=params)
        id_list = resp.json().get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return []
            
        # Fetch details
        fetch_url = f"{base_url}esummary.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        fetch_resp = requests.get(fetch_url, params=fetch_params)
        results = fetch_resp.json().get("result", {})
        
        for pmid in id_list:
            summary = results.get(pmid, {})
            if not summary: continue
            
            papers.append(normalize_paper({
                "title": summary.get("title"),
                "authors": [a.get("name") for a in summary.get("authors", [])],
                "published_date": summary.get("pubdate"),
                "pmid": pmid,
                "doi": summary.get("elocationid") if "doi:" in summary.get("elocationid", "") else None
            }, "PubMed"))
            
    except Exception as e:
        print(f"Error fetching from PubMed: {e}")
        
    return papers

def fetch_semantic_scholar_papers(query: str, max_results: int = 5, source_filter: Optional[str] = None) -> List[Dict]:
    """Fetch from Semantic Scholar."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY
        
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,authors,year,url,externalIds,venue,publicationDate"
    }
    
    papers = []
    try:
        # Add a small delay for public API
        if not settings.SEMANTIC_SCHOLAR_API_KEY:
            time.sleep(1.0)
            
        resp = requests.get(url, params=params, headers=headers)
        
        # Simple retry for 429 if no key
        if resp.status_code == 429 and not settings.SEMANTIC_SCHOLAR_API_KEY:
            time.sleep(3.0)
            resp = requests.get(url, params=params, headers=headers)
            
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for item in data:
                # If we filter by source (e.g. bioRxiv), check venue or external IDs
                if source_filter:
                    venue = str(item.get("venue", "")).lower()
                    if source_filter.lower() not in venue:
                        continue
                
                ext_ids = item.get("externalIds", {})
                papers.append(normalize_paper({
                    "title": item.get("title"),
                    "abstract": item.get("abstract"),
                    "authors": item.get("authors"),
                    "year": item.get("year"),
                    "url": item.get("url"),
                    "doi": ext_ids.get("DOI"),
                    "paperId": item.get("paperId")
                }, source_filter or "Semantic Scholar"))
        else:
            print(f"S2 API returned {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Error fetching from Semantic Scholar: {e}")
        
    return papers

def apply_quality_filters(papers: List[Dict]) -> List[Dict]:
    """
    Apply hard filters (abstract) and compute heuristic relevance scores.
    Conservative filtering: keep papers unless abstract is missing.
    """
    filtered_papers = []
    
    aging_keywords = [
        "aging", "senescence", "cellular senescence", "age-related", 
        "longevity", "ovarian aging", "inflammaging", "epigenetic drift", 
        "mitochondrial dysfunction", "proteostasis", "DNA damage"
    ]
    
    synbio_keywords = [
        "synthetic biology", "genetic circuit", "gene circuit", 
        "engineered cells", "biosensor", "reporter", "regulation circuit", 
        "cellular computation", "signal processing", "engineering biology", 
        "circuit design"
    ]

    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        
        # 1. Hard filter: Abstract required
        # Some sources return placeholders like "No abstract available."
        is_missing_abstract = not abstract or len(abstract) < 50 or "no abstract available" in abstract
        
        if is_missing_abstract:
            print(f"  [Filter] Skipped: {paper['title'][:50]}... (Reason: Missing or empty abstract)")
            continue

        # 2. Compute heuristic scores
        aging_score = sum(1 for kw in aging_keywords if kw in title or kw in abstract)
        synbio_score = sum(1 for kw in synbio_keywords if kw in title or kw in abstract)
        
        # Store scores for logging/ranking
        paper["aging_relevance_score"] = aging_score
        paper["synbio_relevance_score"] = synbio_score
        
        # Log results
        status = "Kept"
        print(f"  [Filter] {status}: {paper['title'][:50]}... (Aging: {aging_score}, SynBio: {synbio_score})")
        
        filtered_papers.append(paper)
        
    return filtered_papers

def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """Deduplicate papers by DOI or normalized title."""
    unique_papers = {}
    
    for paper in papers:
        # Use DOI as primary key
        key = paper.get("doi")
        if not key:
            # Fallback to normalized title
            key = re.sub(r'[^a-zA-Z0-9]', '', paper["title"].lower())
            
        if key not in unique_papers:
            unique_papers[key] = paper
        else:
            # Keep the one with an abstract or better metadata
            existing = unique_papers[key]
            if len(paper["abstract"]) > len(existing["abstract"]):
                unique_papers[key] = paper
                
    return list(unique_papers.values())

def rank_papers(papers: List[Dict]) -> List[Dict]:
    """Heuristic ranking using source priority, keywords, and recency."""
    source_priority = {
        "PubMed": 10,
        "bioRxiv": 8,
        "Semantic Scholar": 5,
        "arXiv": 3
    }
    
    for paper in papers:
        score = source_priority.get(paper["source"], 0)
        
        # Use pre-computed heuristic scores from apply_quality_filters
        score += paper.get("aging_relevance_score", 0) * 2
        score += paper.get("synbio_relevance_score", 0) * 2
        
        # Recency boost
        if paper["published_date"]:
            try:
                match = re.search(r'\d{4}', str(paper["published_date"]))
                if match:
                    year = int(match.group())
                    current_year = datetime.now().year
                    score += max(0, 5 - (current_year - year))
            except:
                pass
                
        paper["relevance_score"] = score
        
    return sorted(papers, key=lambda x: x["relevance_score"], reverse=True)

def fetch_recent_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Refactored main entry point for the pipeline.
    Uses multi-source retrieval and ranking.
    """
    print(f"Starting multi-source retrieval for: {query}")
    
    # Use expanded queries if available in settings, else use the provided query
    queries = getattr(settings, "EXPANDED_QUERIES", [query])
    all_raw_papers = []
    
    # Simple per-source cap to keep it modest
    per_source_cap = 5
    
    for q in queries:
        print(f"  Searching: {q}")
        all_raw_papers.extend(fetch_pubmed_papers(q, per_source_cap))
        
        if settings.ENABLE_SEMANTIC_SCHOLAR:
            all_raw_papers.extend(fetch_semantic_scholar_papers(q, per_source_cap, source_filter="bioRxiv"))
            all_raw_papers.extend(fetch_semantic_scholar_papers(q, per_source_cap))
        else:
            if q == queries[0]: # Only log once
                print("  Semantic Scholar is disabled (ENABLE_SEMANTIC_SCHOLAR=false). Skipping.")
        
        all_raw_papers.extend(fetch_arxiv_papers(q, per_source_cap))
        
    print(f"Total raw papers retrieved: {len(all_raw_papers)}")
    
    deduplicated = deduplicate_papers(all_raw_papers)
    print(f"After deduplication: {len(deduplicated)} papers")
    
    print("\nApplying quality filters...")
    filtered = apply_quality_filters(deduplicated)
    print(f"After filtering: {len(filtered)} papers")
    
    ranked = rank_papers(filtered)
    
    final_selection = ranked[:max_results]
    
    print("\nFinal Selected Papers:")
    for idx, p in enumerate(final_selection):
        print(f"{idx+1}. [{p['source']}] {p['title'][:80]}... (Score: {p['relevance_score']})")
        
    return final_selection
