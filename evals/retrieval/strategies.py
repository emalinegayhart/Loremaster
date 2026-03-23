STRATEGIES = {
    "original": {
        "query": lambda q: {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^4", "summary^2", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "minimum_should_match": "75%",
                }
            }
        }
    },

    "cross_fields": {
        "query": lambda q: {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^4", "summary^2", "content"],
                    "type": "cross_fields",
                }
            }
        }
    },

    "best_fields": {
        "query": lambda q: {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^4", "summary^2", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        }
    },

    "rrf_bm25": {
        "query": lambda q: {
            "retriever": {
                "rrf": {
                    "retrievers": [
                        {
                            "standard": {
                                "query": {
                                    "multi_match": {
                                        "query": q,
                                        "fields": ["title^4", "summary^2", "content"],
                                        "type": "cross_fields",
                                    }
                                }
                            }
                        },
                        {
                            "standard": {
                                "query": {
                                    "multi_match": {
                                        "query": q,
                                        "fields": ["title^4", "summary^2", "content"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            }
                        },
                    ],
                    "rank_window_size": 50,
                    "rank_constant": 20,
                }
            }
        }
    },

    "rrf_elser": {
        "query": lambda q: {
            "retriever": {
                "rrf": {
                    "retrievers": [
                        {
                            "standard": {
                                "query": {
                                    "multi_match": {
                                        "query": q,
                                        "fields": ["title^4", "summary^2", "content"],
                                        "type": "cross_fields",
                                    }
                                }
                            }
                        },
                        {
                            "standard": {
                                "query": {
                                    "multi_match": {
                                        "query": q,
                                        "fields": ["title^4", "summary^2", "content"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            }
                        },
                        {
                            "standard": {
                                "query": {
                                    "sparse_vector": {
                                        "field": "content_sparse",
                                        "inference_id": ".elser_model_2_linux-x86_64",
                                        "query": q,
                                    }
                                }
                            }
                        },
                    ],
                    "rank_window_size": 50,
                    "rank_constant": 20,
                }
            }
        }
    },
}
