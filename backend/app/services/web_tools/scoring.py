"""Relevance scoring for scraped articles."""

import re


def score_relevance(title: str, content: str, topic: str) -> float:
    """Score how relevant an article is to the given topic (0.0–1.0)."""
    kws = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 2]
    if not kws:
        return 0.5
    t_hits = sum(1 for k in kws if k in title.lower())
    c_hits = sum(1 for k in kws if k in content[:2000].lower())
    score = (t_hits / len(kws)) * 0.4 + (c_hits / len(kws)) * 0.6
    # Bonus for longer articles (more substance)
    if len(content) > 3000:
        score = min(1.0, score + 0.1)
    return round(min(1.0, score), 3)
