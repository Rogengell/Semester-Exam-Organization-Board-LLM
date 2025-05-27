def calc_expected_time(optimistic: float, most_likely: float, pessimistic: float) -> float:
    return round((optimistic + (4 * most_likely) + pessimistic) / 6, 2)