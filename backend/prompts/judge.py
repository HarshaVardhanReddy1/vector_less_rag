def generate_llm_judge_prompt(query: str, answer: str, context: str) -> str:
    return f"""You are a strict, impartial answer quality judge.

Evaluate the generated answer against the user query and retrieved context.
Score three metrics on a scale of 0.0 to 1.0 (rounded to 2 decimal places).

--------------------------------------------------
METRIC 1: FAITHFULNESS (Groundedness & Absence of Hallucination)
--------------------------------------------------

Measures: Every claim in the answer is directly supported by the context.
PENALTIES for:
- Unsubstantiated claims: statements not found or implied in context (hallucination).
- Inferred information: answers combining context in ways requiring external knowledge.
- Rephrasing as fact: rewording context vaguely or incorrectly (context shift).
- Assumed context: treating unstated context as given (e.g., "they decided..." when
  decision-maker not mentioned).

Scoring:
1.0 = Every statement can be traced to specific text in context. Zero fabrication.
0.8 = Nearly all claims directly supported; 1-2 minor inferences or slight rewording.
0.5 = Roughly half the answer is directly supported; other half is inferred or absent.
0.2 = Most claims lack clear support; mostly inferred or outside context.
0.0 = Extensive hallucination; core claims contradict or cannot be found in context.

--------------------------------------------------
METRIC 2: RELEVANCE (Query Satisfaction)
--------------------------------------------------

Measures: How well does the answer address the user's specific question?
PENALTIES for:
- Incomplete answers: significant parts of query left unanswered.
- Off-topic content: information not requested by the query.
- Shallow answers: surface-level information when details were requested.
- Missing key components: e.g., query asks for "why and how" but answer only provides "what".

Scoring:
1.0 = Fully answers the query; nothing important left out; zero off-topic content.
0.8 = Answers most of the query; minor gaps or slight tangential content.
0.5 = Partially answers query; significant gaps or notable off-topic content.
0.2 = Barely addresses query; mostly irrelevant or vague.
0.0 = Does not answer the query at all.

--------------------------------------------------
METRIC 3: CONTEXT PRECISION (Conciseness & Relevance)
--------------------------------------------------

Measures: Does the answer extract only relevant context, without padding or noise?
PENALTIES for:
- Verbose padding: unnecessary elaboration beyond what the query requires.
- Redundancy: repeating the same information multiple ways.
- Irrelevant context: including sections/details not needed for the answer.
- Filler language: "As the context states...", connector phrases, boilerplate.

Scoring:
1.0 = Precise extraction; uses only relevant context; zero padding or redundancy.
0.8 = Mostly precise; 1-2 minor redundancies or unnecessary sentences.
0.5 = Moderate padding; some irrelevant context included; some redundancy.
0.2 = Verbose; excessive padding; more irrelevant than relevant content.
0.0 = Almost entirely padding/noise with minimal actual answer.

--------------------------------------------------
JUDGMENT RULES
--------------------------------------------------

**CRITICAL:** Do NOT give high scores across the board. Evaluate each dimension
independently and critically. An answer can be highly relevant but low on
faithfulness if it includes hallucinated details.

**HALLUCINATION is the top concern:** Any unsubstantiated claim immediately reduces
faithfulness score. If answer says "X" but context only implies it, mark as inferred.

**Incomplete context does NOT justify hallucination:** If context is missing details
the query asks for, the answer should state "This information is not in the provided
sections" rather than guess or infer.

--------------------------------------------------
OUTPUT FORMAT (ONLY valid JSON, no markdown)
--------------------------------------------------

{{
  "faithfulness_score": 0.85,
  "relevance_score": 0.92,
  "context_precision_score": 0.78,
  "confidence": "high",
  "reasoning": "Answer is mostly grounded but includes one unsupported claim about X. Fully addresses query. Slightly verbose with one redundant section."
}}

confidence field: "high" (scores 0.8+), "medium" (0.5-0.79), or "low" (below 0.5)
reasoning: Single sentence (max 30 words) summarizing strengths and weaknesses.

--------------------------------------------------
EVALUATION CONTEXT
--------------------------------------------------

QUERY:
{query}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}"""
