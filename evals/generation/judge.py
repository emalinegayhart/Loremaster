import json
import anthropic

JUDGE_PROMPT = """You are evaluating a World of Warcraft lore assistant's response.

Question: {question}
Reference answer: {reference}
Raw source snippets the model was given:
{snippets}
Model response: {response}

Score the response on three dimensions from 1 to 5. Higher is always better.

- correctness: is the answer factually accurate compared to the reference?
- faithfulness: does the answer stick to what was retrieved rather than inventing details?
- relevance: does the answer actually address the question asked?

Return only a JSON object with no other text:
{{"correctness": <1-5>, "faithfulness": <1-5>, "relevance": <1-5>, "reasoning": "<one sentence>"}}"""

NARRATIVE_SCORE_PROMPT = """Score the following text on how narrative it is, from 1 to 5.

1 = dry, structured, or list-like — facts stated plainly with no connective prose
3 = mixed — some flowing sentences but also structured or fragmented sections
5 = fully narrative — written in continuous, engaging prose with cause and effect and a clear voice

Text:
{text}

Return only a JSON object with no other text:
{{"narrative_score": <1-5>, "reasoning": "<one sentence>"}}"""


def score(question: str, reference: str, snippets: list[str], response: str, client: anthropic.Anthropic) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question,
            reference=reference,
            snippets="\n---\n".join(snippets),
            response=response,
        )}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def score_narrative(text: str, client: anthropic.Anthropic) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=128,
        messages=[{"role": "user", "content": NARRATIVE_SCORE_PROMPT.format(text=text)}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)
