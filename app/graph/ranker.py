class GraphRanker:
    def personalized_pagerank(self, graph, seed_nodes: list[str], top_k: int = 20) -> list[tuple[str, float]]:
        try:
            import networkx as nx
        except ImportError:
            return []
        if not seed_nodes:
            return []
        personalization = {node: 0.0 for node in graph.nodes}
        for node in seed_nodes:
            if node in personalization:
                personalization[node] = 1.0
        if not any(personalization.values()):
            return []
        scores = nx.pagerank(graph, personalization=personalization)
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
