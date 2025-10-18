"""
Citation-Aware Prompt Template

Similar to Material Studio Expert Prompt - ensures citations and source attribution
"""

# This is the Material Studio expert prompt that already exists in api/chat.py
# We're creating a generic version here for reusability

CITATION_TEMPLATE = """You are an expert technical assistant. Answer questions using ONLY the retrieved documentation provided below.

Core Principles:
1. **Accuracy**: Use ONLY information from the provided context
2. **Citations**: Always cite specific sources when making claims
3. **Transparency**: Acknowledge when information is insufficient
4. **No Hallucination**: Never generate information not in the context

Retrieved Context:
{context}

User Question: {question}

Instructions:
- Answer the question using the context above
- Cite sources using [Source X] notation
- If the context doesn't contain the answer, clearly state: "I don't have sufficient information to answer this question."
- Provide clear, concise explanations
- Include relevant code examples or parameters from the context

Answer:
"""

# Citation template with numbered sources
NUMBERED_CITATION_TEMPLATE = """You are a helpful assistant. Answer the question using the provided sources.

Sources:
{numbered_sources}

Question: {question}

Instructions:
- Reference sources using [1], [2], [3] notation
- Combine information from multiple sources when relevant
- If sources don't contain the answer, say so explicitly

Answer with citations:
"""

# Academic citation style
ACADEMIC_CITATION_TEMPLATE = """Provide a well-researched answer to the following question using the provided literature.

Literature:
{context}

Research Question: {question}

Requirements:
- Cite all claims using (Author, Year) or (Document Title, Section)
- Synthesize information from multiple sources
- Acknowledge limitations or gaps in the literature
- Use formal academic tone

Response:
"""


def build_citation_prompt(
    question: str,
    context: str,
    template: str = CITATION_TEMPLATE
) -> str:
    """
    Build a citation-aware prompt

    Args:
        question: User question
        context: Retrieved context documents
        template: Citation template to use

    Returns:
        Formatted prompt
    """
    return template.format(
        question=question,
        context=context
    )


def build_numbered_citation_prompt(
    question: str,
    context_chunks: list
) -> str:
    """
    Build citation prompt with numbered sources

    Args:
        question: User question
        context_chunks: List of dicts with 'content', 'title', 'page' fields

    Returns:
        Formatted prompt with numbered sources
    """
    # Format sources with numbers
    numbered_sources_parts = []

    for i, chunk in enumerate(context_chunks, 1):
        content = chunk.get('content', '')
        title = chunk.get('title', 'Document')
        page = chunk.get('page', 'N/A')
        source = chunk.get('source', 'Unknown')

        numbered_sources_parts.append(
            f"[{i}] {title} (Page {page}, Source: {source}):\n{content}\n"
        )

    numbered_sources = "\n".join(numbered_sources_parts)

    return NUMBERED_CITATION_TEMPLATE.format(
        question=question,
        numbered_sources=numbered_sources
    )


def extract_citations(response: str) -> list:
    """
    Extract citation markers from response

    Args:
        response: LLM response with citations

    Returns:
        List of cited source numbers/references
    """
    import re

    # Pattern: [1], [2], [3] or [Source 1], etc.
    citation_patterns = [
        r'\[(\d+)\]',  # [1], [2], etc.
        r'\[Source (\d+)\]',  # [Source 1], etc.
        r'\(Source:\s*([^)]+)\)',  # (Source: Title)
    ]

    citations = []

    for pattern in citation_patterns:
        matches = re.findall(pattern, response)
        citations.extend(matches)

    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for citation in citations:
        if citation not in seen:
            seen.add(citation)
            unique_citations.append(citation)

    return unique_citations


def validate_citations(
    response: str,
    num_sources: int
) -> dict:
    """
    Validate that citations are used correctly

    Args:
        response: LLM response
        num_sources: Number of sources provided

    Returns:
        Dict with validation results
    """
    citations = extract_citations(response)

    # Check if any citations used
    has_citations = len(citations) > 0

    # Check if all sources were cited
    cited_sources = set(citations)
    all_sources_cited = len(cited_sources) == num_sources

    # Check for invalid citations (citing non-existent sources)
    invalid_citations = []
    for citation in citations:
        try:
            source_num = int(citation)
            if source_num < 1 or source_num > num_sources:
                invalid_citations.append(citation)
        except ValueError:
            # Non-numeric citation (e.g., document name)
            pass

    return {
        'has_citations': has_citations,
        'num_citations': len(citations),
        'unique_sources_cited': len(cited_sources),
        'all_sources_cited': all_sources_cited,
        'invalid_citations': invalid_citations,
        'citations': citations
    }


def format_response_with_references(
    response: str,
    sources: list
) -> str:
    """
    Format response with a references section

    Args:
        response: LLM response with [1], [2] citations
        sources: List of source dicts

    Returns:
        Formatted response with References section
    """
    citations = extract_citations(response)

    if not citations:
        return response

    # Build references section
    references_parts = [
        "\n\n## References\n"
    ]

    for citation in citations:
        try:
            idx = int(citation) - 1  # Convert to 0-indexed
            if 0 <= idx < len(sources):
                source = sources[idx]
                title = source.get('title', 'Unknown')
                page = source.get('page', 'N/A')
                source_name = source.get('source', 'Unknown')

                references_parts.append(
                    f"[{citation}] {title}, Page {page} ({source_name})"
                )
        except (ValueError, IndexError):
            continue

    if len(references_parts) > 1:
        return response + "\n".join(references_parts)

    return response


# Example usage
if __name__ == "__main__":
    # Test citation prompt
    question = "How does the Nosé-Hoover thermostat work?"

    context = """
    Temperature Control in Molecular Dynamics:

    The Nosé-Hoover thermostat is a deterministic method for controlling temperature
    in molecular dynamics simulations. It introduces an additional degree of freedom
    that acts as a heat reservoir, allowing the system to exchange energy and maintain
    a target temperature.

    Implementation in Forcite:
    - Set ensemble to NVT (constant Number, Volume, Temperature)
    - Specify target temperature (e.g., 300 K)
    - Choose thermostat type: Nosé-Hoover
    - Set time constant (typically 0.1-1.0 ps)

    The thermostat ensures proper canonical ensemble sampling while preserving
    the deterministic nature of classical molecular dynamics.
    """

    # Basic citation prompt
    prompt = build_citation_prompt(question, context)

    print("=== Citation-Aware Prompt ===")
    print(prompt)
    print("\n" + "="*50 + "\n")

    # Numbered citation prompt
    context_chunks = [
        {
            'content': context,
            'title': 'Temperature Control Methods',
            'page': 15,
            'source': 'Forcite User Guide'
        }
    ]

    numbered_prompt = build_numbered_citation_prompt(question, context_chunks)

    print("=== Numbered Citation Prompt ===")
    print(numbered_prompt)
    print("\n" + "="*50 + "\n")

    # Test citation extraction
    sample_response = """
    The Nosé-Hoover thermostat [1] is a deterministic temperature control method
    used in molecular dynamics. According to the documentation [1], it introduces
    an additional degree of freedom that acts as a heat reservoir.

    Implementation requires setting the ensemble to NVT [1] and specifying parameters
    such as target temperature and time constant.
    """

    citations = extract_citations(sample_response)

    print("=== Extracted Citations ===")
    print(f"Citations found: {citations}")
    print("\n" + "="*50 + "\n")

    # Validate citations
    validation = validate_citations(sample_response, num_sources=1)

    print("=== Citation Validation ===")
    for key, value in validation.items():
        print(f"{key}: {value}")
    print("\n" + "="*50 + "\n")

    # Format with references
    formatted = format_response_with_references(sample_response, context_chunks)

    print("=== Formatted Response with References ===")
    print(formatted)
