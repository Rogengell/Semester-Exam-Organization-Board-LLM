def calc_expected_time(Optimistic: float, MostLikely: float, Pessimistic: float) -> float:
    return round((Optimistic + (4 * MostLikely) + Pessimistic) / 6, 2)