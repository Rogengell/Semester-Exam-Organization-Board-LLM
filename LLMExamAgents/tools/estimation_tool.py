from LLMExamAgents.config import LLM_CONFIG
from autogen import AssistantAgent
import re


def estimation_tool(text: str) -> dict[str, float]:
    """
    **Estimates task duration based on a detailed description of the task.**
    Returns a dictionary with 'Optimistic', 'MostLikely', and 'Pessimistic' estimates in hours.
    Requires a single string input: `text` (the task description).
    """
    agent = AssistantAgent(
        name="Time Estimation Agent",
        system_message="""
        You are a helpful AI assistant. 
        Your job is to estimate task durations using prior knowledge, known patterns, and examples given below based on the provided description.

        For each task input, return:
        Optimistic: <number of hours>
        MostLikely: <number of hours>
        Pessimistic: <number of hours>
        """,
        llm_config=LLM_CONFIG,
    )
    reply = agent.generate_reply(
        messages=[
            {"role": "user", "content": f'estimate the time for the following task: {text}'}
        ],
    )

    content = reply["content"] if isinstance(reply, dict) else reply

    if content.strip().upper() == "TERMINATE":
        return {"Optimistic": 0, "MostLikely": 0, "Pessimistic": 0}
    
    # Parse using regex
    pattern = r"Optimistic\s*:\s*(\d+\.?\d*)\s*MostLikely\s*:\s*(\d+\.?\d*)\s*Pessimistic\s*:\s*(\d+\.?\d*)"
    match = re.search(pattern, content.replace('\n', ' '), re.IGNORECASE)

    if not match:
        raise ValueError("No reply found")

    return{
        "Optimistic": float(match.group(1)),
        "MostLikely": float(match.group(2)),
        "Pessimistic": float(match.group(3))
    }

