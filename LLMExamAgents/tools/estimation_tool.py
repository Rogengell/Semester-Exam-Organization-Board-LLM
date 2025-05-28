from LLMExamAgents.config import LLM_CONFIG
from autogen import AssistantAgent
import re
import json
from pathlib import Path
from typing import Dict

def calc_expected_time(Optimistic: float, MostLikely: float, Pessimistic: float) -> float:
    """
    **Calculates the PERT (Program Evaluation and Review Technique) expected time.**
    Requires three float inputs: `Optimistic`, `MostLikely`, and `Pessimistic` durations in hours.
    Returns a single float representing the rounded expected time.
    """
    return round(((Optimistic + (4 * MostLikely) + Pessimistic) / 6), 2)


def estimation_tool(text: str) -> dict[str, float]:
    """
    Returns PERT based time estimates using nearest match from task DB
    """
    agent = AssistantAgent(
        name="Time Estimation Agent",
        system_message="You are an expert task planner, estimating task duration based on a description. ",
        llm_config=LLM_CONFIG,
    )

    estimation_prompt = f"""
    You are estimating the times in hours for a task from a description.

    Be realistic how long it will take for an average software developer. Do not invent extreme or random values.

    Do NOT invent or interpolate any other values under any circumstances.

    Be sure to:
    
    You may generalize, extrapolate, or interpolate based on task similarity, complexity, and scope.
    Avoid extreme values unless the task clearly warrants it.
    Ensure your estimates are reasonable and justifiable in comparison to the examples.,

    The Description: {text}

    Return ONLY:

    
    Optimistic: <number>
    MostLikely: <number>
    Pessimistic: <number>,

    Do only two iterations of estimation.
    **Do NOT overwrite any results with new results.**
    Do not return ExpectedTime; it will be calculated separately.
    Do not add any explanation or reasoning.
    """
    reply = agent.generate_reply(
        messages=[
            {"role": "user", "content": estimation_prompt}
        ],
    )

    content = reply["content"] if isinstance(reply, dict) else reply

    if content.strip().upper() == "TERMINATE":
        return {"Optimistic": 0, "MostLikely": 0, "Pessimistic": 0, "ExpectedTime": 0}
    
    # Parse using regex
    pattern = (
    r"Optimistic\s*:\s*(\d+\.?\d*)"
    r".*?"
    r"MostLikely\s*:\s*(\d+\.?\d*)"
    r".*?"
    r"Pessimistic\s*:\s*(\d+\.?\d*)"
    )
    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

    if not match:
        raise ValueError("No reply found")
    


    optimistic = float(match.group(1))
    most_likely = float(match.group(2))
    pessimistic = float(match.group(3))
    print(f"Parsed values: Optimistic={optimistic}, MostLikely={most_likely}, Pessimistic={pessimistic}")
    expected_time = calc_expected_time(optimistic, most_likely, pessimistic)
    

    return{
        "Optimistic": optimistic,
        "MostLikely": most_likely,
        "Pessimistic": pessimistic,
        "ExpectedTime": expected_time
    }

