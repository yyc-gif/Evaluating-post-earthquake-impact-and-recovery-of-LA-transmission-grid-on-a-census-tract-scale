"""Canonical reader-facing restoration-strategy names."""

CANONICAL_STRATEGY_ORDER = [
    "centrality-first",
    "impact-first",
    "betweenness-first",
    "degree-first",
    "closeness-first",
    "hospital-first",
    "random",
    "GA_Balanced",
    "GA_HospFirst",
    "GA_Efficiency",
]

CANONICAL_STRATEGY_LABELS = {
    "centrality-first": "Impact \u03bb2 first",
    "impact-first": "Impact population first",
    "betweenness-first": "Betweenness first",
    "degree-first": "Degree first",
    "closeness-first": "Closeness first",
    "hospital-first": "Hospital first",
    "random": "Random",
    "GA_Balanced": "GA-Balanced",
    "GA_HospFirst": "GA-HospitalFirst",
    "GA_Efficiency": "GA-Efficiency",
}

CANONICAL_STRATEGY_DISPLAY_ORDER = [
    CANONICAL_STRATEGY_LABELS[key] for key in CANONICAL_STRATEGY_ORDER
]

# Stage 6 recovery/topology figures use the descriptive legend supplied for
# those two plot families only. Other figures and exported Strategy fields keep
# the compact canonical labels above.
STAGE6_LEGEND_ORDER = [
    "centrality-first",
    "betweenness-first",
    "impact-first",
    "degree-first",
    "closeness-first",
    "hospital-first",
    "random",
    "GA_Balanced",
    "GA_HospFirst",
    "GA_Efficiency",
]

STAGE6_LEGEND_LABELS = {
    "centrality-first": "Impact λ2 (Grid Topology) First",
    "betweenness-first": "Betweenness First (Bridges)",
    "impact-first": "Impact (Population) First",
    "degree-first": "Degree First (Hubs)",
    "closeness-first": "Closeness First (Accessibility)",
    "hospital-first": "Hospital First (Critical Nodes)",
    "random": "Random Baseline",
    "GA_Balanced": "GA (Balanced)",
    "GA_HospFirst": "GA (HospitalFirst)",
    "GA_Efficiency": "GA (Efficiency)",
}

STAGE6_LEGEND_DISPLAY_ORDER = [
    STAGE6_LEGEND_LABELS[key] for key in STAGE6_LEGEND_ORDER
]


def canonical_strategy_key(value: object) -> str | None:
    """Resolve internal, legacy, or canonical text to one strategy key."""
    text = str(value).strip()
    lower = text.lower()

    for key, label in CANONICAL_STRATEGY_LABELS.items():
        if lower == label.lower():
            return key

    if "ga" in lower:
        if "balanced" in lower:
            return "GA_Balanced"
        if "hospitalfirst" in lower or "hospfirst" in lower:
            return "GA_HospFirst"
        if "efficiency" in lower:
            return "GA_Efficiency"

    if "centrality-first" in lower or "lambda2" in lower or "\u03bb2" in lower:
        return "centrality-first"
    if "impact-first" in lower or "impact population" in lower:
        return "impact-first"
    if "betweenness" in lower:
        return "betweenness-first"
    if "degree" in lower:
        return "degree-first"
    if "closeness" in lower:
        return "closeness-first"
    if "hospital" in lower:
        return "hospital-first"
    if "random" in lower:
        return "random"
    return None


def canonical_strategy_label(value: object) -> str:
    """Return the canonical reader-facing label for a strategy."""
    key = canonical_strategy_key(value)
    if key is not None:
        return CANONICAL_STRATEGY_LABELS[key]

    text = str(value).strip()
    lower = text.lower()
    if "theoretical" in lower or "unconstrained" in lower or "stage3" in lower:
        return "Theoretical limit"
    return text


def stage6_legend_label(value: object) -> str:
    """Return the descriptive label used only in Stage 6 recovery/dual plots."""
    key = canonical_strategy_key(value)
    if key is not None:
        return STAGE6_LEGEND_LABELS[key]
    return canonical_strategy_label(value)
