"""
Extractive QA Prompt Template

Returns only exact quotes from context - prevents hallucination
"""

EXTRACTIVE_TEMPLATE = """You are an extractive question answering system. Your task is to find and return ONLY exact text passages from the provided context that answer the question.

IMPORTANT RULES:
1. Return ONLY direct quotes from the context
2. Do NOT paraphrase or add your own words
3. If the answer is not in the context, respond with: "Information not available in the provided context."
4. Quote relevant passages verbatim
5. You may combine multiple relevant quotes

Context:
{context}

Question: {question}

Relevant Passages (direct quotes only):
"""

# Alternative: Structured extractive format
STRUCTURED_EXTRACTIVE_TEMPLATE = """Extract relevant information from the context to answer the question. Provide direct quotes only.

Context:
{context}

Question: {question}

Response Format:
- Quote 1: [exact text from context]
- Quote 2: [exact text from context]
- ...

If no relevant information exists, respond with: "No relevant information found."

Extracted Information:
"""

# Extractive with source attribution
ATTRIBUTED_EXTRACTIVE_TEMPLATE = """Find relevant information in the context and quote it exactly, including the source.

{context_with_sources}

Question: {question}

Instructions:
- Provide exact quotes only
- Include source for each quote
- Format: "[Quote text]" (Source: [source name], Page [page])

Relevant Quotes:
"""


def build_extractive_prompt(
    question: str,
    context: str,
    template: str = EXTRACTIVE_TEMPLATE
) -> str:
    """
    Build an extractive QA prompt

    Args:
        question: User question
        context: Retrieved context documents
        template: Extractive template to use

    Returns:
        Formatted prompt
    """
    return template.format(
        question=question,
        context=context
    )


def build_extractive_prompt_with_sources(
    question: str,
    context_chunks: list
) -> str:
    """
    Build extractive prompt with source attribution

    Args:
        question: User question
        context_chunks: List of dicts with 'content', 'source', 'page' fields

    Returns:
        Formatted prompt with sources
    """
    # Format context with sources
    context_parts = []

    for i, chunk in enumerate(context_chunks, 1):
        content = chunk.get('content', '')
        source = chunk.get('source', 'Unknown')
        page = chunk.get('page', 'N/A')
        title = chunk.get('title', 'Document')

        context_parts.append(
            f"[Source {i}] {title} (Page {page}):\n{content}\n"
        )

    context_with_sources = "\n".join(context_parts)

    return ATTRIBUTED_EXTRACTIVE_TEMPLATE.format(
        question=question,
        context_with_sources=context_with_sources
    )


def parse_extractive_response(response: str) -> dict:
    """
    Parse extractive QA response into structured format

    Args:
        response: LLM response text

    Returns:
        Dict with 'has_answer', 'quotes', 'sources'
    """
    # Check if information was found
    not_found_patterns = [
        "information not available",
        "no relevant information",
        "not found in the context",
        "cannot find"
    ]

    response_lower = response.lower()
    has_answer = not any(pattern in response_lower for pattern in not_found_patterns)

    if not has_answer:
        return {
            'has_answer': False,
            'quotes': [],
            'sources': [],
            'message': "Information not available in the provided context."
        }

    # Extract quotes (text in quotes)
    import re

    # Pattern: text between quotes
    quote_pattern = r'"([^"]+)"'
    quotes = re.findall(quote_pattern, response)

    # Pattern: Source attribution
    source_pattern = r'\(Source:\s*([^,)]+)(?:,\s*Page\s*([^)]+))?\)'
    sources = re.findall(source_pattern, response)

    return {
        'has_answer': True,
        'quotes': quotes,
        'sources': sources,
        'raw_response': response
    }


def validate_extractive_answer(
    answer: str,
    context: str,
    min_overlap: float = 0.8
) -> bool:
    """
    Validate that the answer is truly extractive (from context)

    Args:
        answer: Generated answer
        context: Original context
        min_overlap: Minimum word overlap ratio required

    Returns:
        True if answer is sufficiently extractive
    """
    if not answer or not context:
        return False

    # Tokenize
    answer_words = set(answer.lower().split())
    context_words = set(context.lower().split())

    # Calculate overlap
    overlap = answer_words & context_words
    overlap_ratio = len(overlap) / len(answer_words) if answer_words else 0

    return overlap_ratio >= min_overlap


# Example usage
if __name__ == "__main__":
    # Test extractive prompt
    question = "What is the recommended timestep for MD simulations?"

    context = """
    Forcite Molecular Dynamics Parameters:

    The time step controls the temporal resolution of the simulation.
    For standard molecular dynamics simulations, the recommended time step is 1.0 femtoseconds (fs).
    Larger time steps may be used for coarse-grained systems, up to 2.0 fs.

    Temperature control is achieved using the Nosé-Hoover thermostat,
    which maintains constant temperature in NVT ensemble simulations.
    """

    # Basic extractive prompt
    prompt = build_extractive_prompt(question, context)

    print("=== Extractive QA Prompt ===")
    print(prompt)
    print("\n" + "="*50 + "\n")

    # Extractive with sources
    context_chunks = [
        {
            'content': context,
            'source': 'Forcite Manual',
            'page': 42,
            'title': 'MD Parameters Guide'
        }
    ]

    prompt_with_sources = build_extractive_prompt_with_sources(question, context_chunks)

    print("=== Extractive QA with Sources ===")
    print(prompt_with_sources)
    print("\n" + "="*50 + "\n")

    # Test response parsing
    sample_response = '''
    "For standard molecular dynamics simulations, the recommended time step is 1.0 femtoseconds (fs)."
    (Source: Forcite Manual, Page 42)
    '''

    parsed = parse_extractive_response(sample_response)

    print("=== Parsed Extractive Response ===")
    print(f"Has Answer: {parsed['has_answer']}")
    print(f"Quotes: {parsed['quotes']}")
    print(f"Sources: {parsed['sources']}")
    print("\n" + "="*50 + "\n")

    # Test validation
    extractive_answer = "the recommended time step is 1.0 femtoseconds"
    hallucinated_answer = "you should use quantum mechanics for this"

    print("=== Validation ===")
    print(f"Extractive answer valid: {validate_extractive_answer(extractive_answer, context)}")
    print(f"Hallucinated answer valid: {validate_extractive_answer(hallucinated_answer, context)}")
