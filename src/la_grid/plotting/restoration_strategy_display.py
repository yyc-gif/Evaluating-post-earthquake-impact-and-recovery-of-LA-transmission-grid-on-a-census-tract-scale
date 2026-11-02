"""Publication-facing labels for frozen restoration strategy identifiers."""

STRATEGY_DISPLAY_NAMES = {
    "centrality-first": "Spectral-connectivity-first",
    "impact-first": "Impact-first",
    "betweenness-first": "Betweenness-first",
    "degree-first": "Degree-first",
    "closeness-first": "Closeness-first",
    "hospital-first": "Hospital-first",
    "vulnerability-first": "Vulnerability-first",
    "random": "Random",
}


def display_name(strategy_id):
    """Return a display label without changing the frozen strategy ID."""
    key = str(strategy_id)
    return STRATEGY_DISPLAY_NAMES.get(key, key)
