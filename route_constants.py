"""Costanti condivise per gradi e punteggi."""

GRADES: tuple[str, ...] = (
    "8C+", "8C", "8B+", "8B", "8A+", "8A", "7C+", "7C", "7B+", "7B",
    "7A+", "7A", "6C+", "6C", "6B+", "6B", "6A+", "6A", "5C+", "5C",
    "5B+", "5B", "5A+", "5A", "4C+", "4C", "4B+", "4B", "4A+", "4A",
)

POINTS_PER_COMPLETED_ROUTE = 10
TAG_THRESHOLDS = (
    ("PRO", 5000),
    ("EXP", 2500),
    ("ADV", 1000),
    ("INT", 500),
    ("BEG", 200),
    ("NEW", 0),
)
