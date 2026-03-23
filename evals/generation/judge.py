import json
import anthropic

JUDGE_PROMPT = """You are evaluating a World of Warcraft lore assistant's response.

Question: {question}
Reference answer: {reference}
Model response: {response}

Score the response on three dimensions from 1 to 5:

- correctness: is the answer factually accurate compared to the reference?
- faithfulness: does the answer stick to what was retrieved rather than inventing details?
- relevance: does the answer actually address the question asked?

Return only a JSON object with no other text:
{{"correctness": <1-5>, "faithfulness": <1-5>, "relevance": <1-5>, "reasoning": "<one sentence>"}}"""


def score(question: str, reference: str, response: str, client: anthropic.Anthropic) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question,
            reference=reference,
            response=response,
        )}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)
