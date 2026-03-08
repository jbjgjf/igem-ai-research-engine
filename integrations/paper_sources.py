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
        # Fetch summary details
        summary_fetch_url = f"{base_url}esummary.fcgi"
        summary_fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        summary_resp = requests.get(summary_fetch_url, params=summary_fetch_params)
        summary_results = summary_resp.json().get("result", {})

        # Fetch full XML for abstracts
        efetch_url = f"{base_url}efetch.fcgi"
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml" # Request XML for full details including abstract
        }
        efetch_resp = requests.get(efetch_url, params=efetch_params)
        
        # Simple regex-based XML abstract extraction to avoid heavy dependencies
        abstract_map = {}
        if efetch_resp.status_code == 200:
            xml_content = efetch_resp.text
            # Use broader regex and DOTALL to find all articles
            articles = re.findall(r"<PubmedArticle>.*?</PubmedArticle>", xml_content, re.DOTALL)
            print(f"  [PubMed Debug] Found {len(articles)} articles in XML")
            
            for article in articles:
                pmid_match = re.search(r"<PMID[^>]*>(\d+)</PMID>", article)
                # Abstracts can have multiple AbstractText segments (Background, Methods, etc.)
                abstract_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", article, re.DOTALL)
                if pmid_match and abstract_parts:
                    pmid = pmid_match.group(1)
                    full_abs = " ".join(abstract_parts)
                    # Strip any remaining XML tags
                    abs_text = re.sub(r"<[^>]+>", "", full_abs).strip()
                    abstract_map[pmid] = abs_text
                    # print(f"  [PubMed Debug] Extracted abstract for {pmid} ({len(abs_text)} chars)")
        
        for pmid in id_list:
            summary = summary_results.get(pmid, {})
            if not summary: continue
            
            abs_text = abstract_map.get(pmid)
            papers.append(normalize_paper({
                "title": summary.get("title"),
                "abstract": abs_text,
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
    """
    filtered_papers = []
    
    # Priority keywords for aging
    aging_keywords = {
        "senescence": 2.0,
        "cellular senescence": 3.0,
        "aging": 1.5,
        "longevity": 1.5,
        "inflammaging": 2.0,
        "epigenetic drift": 2.0,
        "mitochondrial dysfunction": 1.5,
        "ovarian aging": 2.0,
        "proteostasis": 1.5,
        "dna damage": 1.0,
        "telomere": 1.5,
        "autophagy": 1.0,
        "stem cell exhaustion": 2.0
    }
    
    # Priority keywords for synthetic biology
    synbio_keywords = {
        "synthetic biology": 3.0,
        "genetic circuit": 3.0,
        "gene circuit": 3.0,
        "engineered cell": 2.0,
        "biosensor": 2.5,
        "cellular computation": 2.5,
        "biological circuit": 2.0,
        "reporter": 1.0,
        "optogenetics": 1.5,
        "crispr": 1.0,
        "transcription factor": 1.0,
        "feedback loop": 2.0,
        "logic gate": 2.0
    }

    print(f"\n--- Filtering Report ({len(papers)} candidates) ---")
    print(f"{'Source':<15} | {'Title':<50} | {'Abs?':<4} | {'Len':<5} | {'Aging':<5} | {'SynBio':<5} | {'Status'}")
    print("-" * 110)

    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        if abstract == "no abstract available.":
            abstract = ""
        
        # 1. Abstract Quality Check
        abs_len = len(abstract)
        is_missing = not abstract or abs_len < settings.ABSTRACT_MIN_LENGTH or "no abstract available" in abstract
        
        # 2. Compute weighted scores
        aging_score = 0.0
        synbio_score = 0.0
        
        # Score Title (much higher weight)
        for kw, weight in aging_keywords.items():
            if kw in title:
                aging_score += weight * settings.TITLE_WEIGHT
        for kw, weight in synbio_keywords.items():
            if kw in title:
                synbio_score += weight * settings.TITLE_WEIGHT
                
        # Score Abstract
        for kw, weight in aging_keywords.items():
            if kw in abstract:
                aging_score += weight
        for kw, weight in synbio_keywords.items():
            if kw in abstract:
                synbio_score += weight

        # Store scores
        paper["aging_relevance_score"] = round(aging_score, 1)
        paper["synbio_relevance_score"] = round(synbio_score, 1)
        
        # Filter Logic
        keep = True
        skip_reason = ""
        
        if is_missing:
            keep = False
            skip_reason = "Missing Abstract"
        elif aging_score < settings.MIN_RELEVANCE_THRESHOLD:
            keep = False
            skip_reason = f"Low Aging Score ({aging_score})"
        elif synbio_score < settings.MIN_RELEVANCE_THRESHOLD:
            keep = False
            skip_reason = f"Low SynBio Score ({synbio_score})"
        
        status = "KEEP" if keep else f"SKIP ({skip_reason})"
        print(f"{paper['source']:<15} | {title[:50]:<50} | {'Yes' if not is_missing else 'No':<4} | {abs_len:<5} | {aging_score:<5.1f} | {synbio_score:<5.1f} | {status}")
        
        if keep:
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
        "PubMed": 15,
        "bioRxiv": 12,
        "Semantic Scholar": 5,
        "arXiv": 3
    }
    
    for paper in papers:
        # 1. Base score from source
        score = source_priority.get(paper["source"], 0)
        
        # 2. Add pre-computed heuristic scores
        # These are already weighted for title vs abstract
        score += paper.get("aging_relevance_score", 0)
        score += paper.get("synbio_relevance_score", 0)
        
        # 3. Recency boost (mild)
        if paper["published_date"]:
            try:
                match = re.search(r'\d{4}', str(paper["published_date"]))
                if match:
                    year = int(match.group())
                    current_year = datetime.now().year
                    score += max(0, 3 - (current_year - year))
            except:
                pass
                
        paper["relevance_score"] = round(score, 1)
        
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
    
    # Final safety: if no papers meet a absolute sanity score, return empty
    # This prevents the "keeping one weak paper" behavior.
    SANITY_THRESHOLD = 15.0 # (Source + Aging + SynBio)
    strong_papers = [p for p in ranked if p["relevance_score"] >= SANITY_THRESHOLD]
    
    if not strong_papers and ranked:
        print(f"\n[Warning] Found {len(ranked)} papers but none met the sanity threshold ({SANITY_THRESHOLD}).")
        print("Returning zero papers to maintain quality over quantity.")
        return []

    final_selection = strong_papers[:max_results]
    
    print(f"\nFinal Selected Papers ({len(final_selection)}):")
    for idx, p in enumerate(final_selection):
        print(f"{idx+1}. [{p['source']}] {p['title'][:80]}...")
        print(f"   (Scores - Total: {p['relevance_score']}, Aging: {p['aging_relevance_score']}, SynBio: {p['synbio_relevance_score']})")
        
    return final_selection
