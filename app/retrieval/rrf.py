from app.schema.models import RetrievalCandidate


def reciprocal_rank_fusion(result_sets: list[list[RetrievalCandidate]], k: int = 60) -> list[RetrievalCandidate]:
    scores: dict[str, float] = {}
    candidates: dict[str, RetrievalCandidate] = {}
    sources: dict[str, set[str]] = {}

    for results in result_sets:
        for rank, candidate in enumerate(results, start=1):
            scores[candidate.id] = scores.get(candidate.id, 0.0) + 1.0 / (k + rank)
            candidates[candidate.id] = candidate
            sources.setdefault(candidate.id, set()).add(candidate.source)

    fused = []
    for candidate_id, score in scores.items():
        source = "+".join(sorted(sources[candidate_id]))
        fused.append(candidates[candidate_id].model_copy(update={"score": score, "source": source}))
    return sorted(fused, key=lambda item: item.score, reverse=True)
