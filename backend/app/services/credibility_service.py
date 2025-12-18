"""
Source credibility scoring service.
"""
from typing import Dict, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class CredibilityService:
    """
    Scores the credibility of web sources.

    Uses domain-based heuristics to assess trustworthiness.
    Future: Add ML-based content analysis.
    """

    # High-trust domains
    ACADEMIC_DOMAINS = {
        ".edu",
        "arxiv.org",
        "scholar.google.com",
        "jstor.org",
        "ieee.org",
        "acm.org",
        "nature.com",
        "science.org",
        "sciencedirect.com",
        "springer.com",
        "wiley.com",
        "plos.org",
        "pubmed.ncbi.nlm.nih.gov",
    }

    NEWS_ORGS = {
        "nytimes.com",
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "theguardian.com",
        "economist.com",
        "wsj.com",
        "washingtonpost.com",
        "npr.org",
        "pbs.org",
    }

    TECH_BLOGS = {
        "github.com",
        "stackoverflow.com",
        "medium.com",
        "dev.to",
        "hackernoon.com",
        "towardsdatascience.com",
        "techcrunch.com",
        "arstechnica.com",
        "wired.com",
        "verge.com",
    }

    # Low-trust indicators
    SUSPICIOUS_DOMAINS = {
        "blogspot.com",
        "wordpress.com",
        "tumblr.com",
        "weebly.com",
    }

    def score_source(
        self, url: str, title: str = "", snippet: str = ""
    ) -> Dict[str, any]:
        """
        Score source credibility (0.0 - 1.0).

        Args:
            url: Source URL
            title: Page title
            snippet: Content snippet

        Returns:
            {
                "score": 0.85,
                "reasons": ["Academic domain", "HTTPS"],
                "source_type": "academic"
            }
        """
        score = 0.5  # Neutral baseline
        reasons = []
        source_type = "general"

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix for matching
            if domain.startswith("www."):
                domain = domain[4:]

            # Domain checks
            if any(d in domain or domain.endswith(d) for d in self.ACADEMIC_DOMAINS):
                score += 0.4
                reasons.append("Academic domain")
                source_type = "academic"
            elif domain in self.NEWS_ORGS:
                score += 0.3
                reasons.append("Reputable news organization")
                source_type = "news"
            elif domain in self.TECH_BLOGS:
                score += 0.2
                reasons.append("Known tech community site")
                source_type = "blog"

            # GitHub repositories get bonus
            if "github.com" in domain and "/blob/" in url:
                score += 0.15
                reasons.append("GitHub repository")
                source_type = "github"

            # Reddit gets lower score but is still useful
            if "reddit.com" in domain:
                score = 0.6
                reasons.append("Community discussion (Reddit)")
                source_type = "reddit"

            # HTTPS
            if parsed.scheme == "https":
                score += 0.1
                reasons.append("Secure connection (HTTPS)")

            # Content length check (substantial content)
            if len(snippet) > 200:
                score += 0.05
                reasons.append("Substantial content preview")

            # Suspicious domains penalty
            if any(d in domain for d in self.SUSPICIOUS_DOMAINS):
                score -= 0.2
                reasons.append("Free blogging platform (less authoritative)")

            # Clamp score between 0 and 1
            score = min(max(score, 0.0), 1.0)

            logger.debug(
                f"Credibility score for {domain}: {score:.2f} ({', '.join(reasons)})"
            )

            return {"score": score, "reasons": reasons, "source_type": source_type}

        except Exception as e:
            logger.error(f"Error scoring source {url}: {e}")
            return {
                "score": 0.5,
                "reasons": ["Could not assess credibility"],
                "source_type": "general",
            }

    def filter_by_credibility(
        self,
        sources: List[Dict],
        min_score: float = 0.5,
        source_types: List[str] = None,
    ) -> List[Dict]:
        """
        Filter sources by minimum credibility score.

        Args:
            sources: List of source dicts with 'credibility_score' key
            min_score: Minimum credibility score (0.0 - 1.0)
            source_types: Optional list of allowed source types

        Returns:
            Filtered list of sources
        """
        filtered = []

        for source in sources:
            # Score check
            if source.get("credibility_score", 0) < min_score:
                continue

            # Source type filter
            if source_types and source.get("source_type") not in source_types:
                continue

            filtered.append(source)

        logger.info(
            f"Filtered {len(sources)} sources to {len(filtered)} (min_score={min_score})"
        )

        return filtered


# Global instance
_credibility_service: CredibilityService | None = None


def get_credibility_service() -> CredibilityService:
    """
    Get the global credibility service instance.

    Returns:
        Credibility service singleton
    """
    global _credibility_service
    if _credibility_service is None:
        _credibility_service = CredibilityService()
    return _credibility_service
