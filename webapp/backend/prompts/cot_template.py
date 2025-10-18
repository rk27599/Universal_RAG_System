"""
Chain-of-Thought (CoT) Prompt Template

Encourages step-by-step reasoning for complex technical questions
"""

COT_TEMPLATE = """You are a helpful technical assistant. Answer the question using the provided context, showing your reasoning step-by-step.

Retrieved Context:
{context}

User Question: {question}

Let's approach this step-by-step:

1. **Understanding the Question**: What is being asked?

2. **Relevant Information**: What information from the context helps answer this?

3. **Analysis**: How does this information connect to the question?

4. **Answer**: Based on the above analysis, what is the complete answer?

Please provide your response following this structure:
"""

# Alternative: Concise CoT for simpler questions
CONCISE_COT_TEMPLATE = """Answer the following question using the provided context. Think through it step by step, then provide a clear answer.

Context:
{context}

Question: {question}

Reasoning:
[Think step-by-step here]

Answer:
[Final answer here]
"""

# CoT for Technical Documentation
TECHNICAL_COT_TEMPLATE = """You are a technical documentation expert. Answer the question about {domain} using the provided documentation.

Documentation:
{context}

Question: {question}

Analysis:
1. **Key Concepts**: What are the relevant technical concepts?
2. **Parameters/Settings**: What parameters or settings are involved?
3. **Implementation**: How should this be implemented?
4. **Best Practices**: What are the recommended practices?

Answer:
"""


def build_cot_prompt(
    question: str,
    context: str,
    template: str = COT_TEMPLATE,
    domain: str = None
) -> str:
    """
    Build a Chain-of-Thought prompt

    Args:
        question: User question
        context: Retrieved context documents
        template: CoT template to use (default: standard COT)
        domain: Optional domain name (e.g., "Material Studio")

    Returns:
        Formatted prompt
    """
    if domain and '{domain}' in template:
        return template.format(
            question=question,
            context=context,
            domain=domain
        )

    return template.format(
        question=question,
        context=context
    )


def build_cot_prompt_with_examples(
    question: str,
    context: str,
    examples: list = None
) -> str:
    """
    Build CoT prompt with few-shot examples

    Args:
        question: User question
        context: Retrieved context
        examples: List of (question, reasoning, answer) tuples

    Returns:
        Formatted prompt with examples
    """
    prompt_parts = [
        "You are a helpful assistant. Answer questions using step-by-step reasoning.",
        ""
    ]

    # Add examples if provided
    if examples:
        prompt_parts.append("Here are some examples:")
        prompt_parts.append("")

        for i, (ex_q, ex_reasoning, ex_answer) in enumerate(examples, 1):
            prompt_parts.append(f"Example {i}:")
            prompt_parts.append(f"Question: {ex_q}")
            prompt_parts.append(f"Reasoning: {ex_reasoning}")
            prompt_parts.append(f"Answer: {ex_answer}")
            prompt_parts.append("")

    # Add actual question
    prompt_parts.extend([
        "Now answer this question:",
        "",
        f"Context:\n{context}",
        "",
        f"Question: {question}",
        "",
        "Reasoning (think step-by-step):",
    ])

    return "\n".join(prompt_parts)


# Example usage
if __name__ == "__main__":
    # Test CoT prompt
    question = "How do I optimize molecular dynamics simulations in Forcite?"

    context = """
    Forcite Module Overview:
    The Forcite module provides molecular dynamics (MD) simulation capabilities.

    Optimization Parameters:
    - Time step: Recommended 1.0 fs for standard MD
    - Cutoff distance: 12.5 Å for non-bonded interactions
    - Temperature control: Use Nosé-Hoover thermostat for NVT ensemble

    Performance Tips:
    - Enable GPU acceleration when available
    - Use efficient force fields (e.g., COMPASS)
    - Minimize system size when possible
    """

    prompt = build_cot_prompt(question, context, domain="Material Studio")

    print("=== Chain-of-Thought Prompt ===")
    print(prompt)
    print("\n" + "="*50 + "\n")

    # Test with examples
    examples = [
        (
            "What is the default timestep?",
            "Looking at the optimization parameters, I see timestep is mentioned.",
            "The recommended timestep is 1.0 fs for standard MD simulations."
        )
    ]

    prompt_with_examples = build_cot_prompt_with_examples(question, context, examples)

    print("=== CoT Prompt with Examples ===")
    print(prompt_with_examples)
