from LLMExamAgents.config import LLM_CONFIG
from autogen import AssistantAgent
import re


def estimation_tool(text: str) -> dict[str, float]:
    agent = AssistantAgent(
        name="Time Estimation Agent",
        system_message="""
        You are a helpful AI assistant. 
        Your job is to estimate task durations using prior knowledge, known patterns, and examples given below based on the provided description.

        Use the following examples to guide your estimates:
        - Create environment: Optimistic 0.5, MostLikely 1, Pessimistic 2.
        - Set up Authentication: Optimistic 1, MostLikely 2, Pessimistic 3.
        - Creating database schema: Optimistic 2, MostLikely 3, Pessimistic 8.
        - Create API endpoints: Optimistic 0.5, MostLikely 1, Pessimistic 4.
        - Create frontend components: Optimistic 3, MostLikely 4, Pessimistic 6.

        For each task input, return:
        Optimistic: <number of hours>
        MostLikely: <number of hours>
        Pessimistic: <number of hours>

        Format your response exactly like this (no text outside):
        Optimistic: 1
        MostLikely: 3
        Pessimistic: 6

        If you cannot confidently estimate, return all values as 0.
        Don't include any other text in your response.
        Return 'terminate' in upper case when the task is done.""",
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

