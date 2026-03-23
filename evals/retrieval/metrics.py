def hit_rate(results: list[list[str]], expected: list[str], k: int = 5) -> float:
    hits = sum(
        1 for titles, exp in zip(results, expected)
        if any(exp.lower() in t.lower() for t in titles[:k])
    )
    return hits / len(results)


def mrr(results: list[list[str]], expected: list[str], k: int = 5) -> float:
    reciprocal_ranks = []
    for titles, exp in zip(results, expected):
        rank = next(
            (i + 1 for i, t in enumerate(titles[:k]) if exp.lower() in t.lower()),
            None,
        )
        reciprocal_ranks.append(1 / rank if rank else 0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)
