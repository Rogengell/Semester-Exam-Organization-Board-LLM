def calc_expected_time(Optimistic: float, MostLikely: float, Pessimistic: float) -> float:
    """
    **Calculates the PERT (Program Evaluation and Review Technique) expected time.**
    Requires three float inputs: `Optimistic`, `MostLikely`, and `Pessimistic` durations in hours.
    Returns a single float representing the rounded expected time.
    """
    return round((Optimistic + (4 * MostLikely) + Pessimistic) / 6, 2)