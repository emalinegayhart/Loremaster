# Metric Definitions

**correctness** — is the answer factually accurate compared to the reference answer? (1-5, higher is better)

**faithfulness** — does the answer stick to what was retrieved rather than inventing details? (1-5, higher is better)

**relevance** — does the answer actually address the question asked? (1-5, higher is better)

**source_score** — how narrative is the retrieved source material? (1-5, higher is more narrative)

**response_score** — how narrative is the model's response? (1-5, higher is more narrative)

**delta** — response_score minus source_score. How much narrative voice the model added beyond what the source contained.
