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

# def load_data(filepath="db_tasks.json"):
#     with open(filepath, "r", encoding="utf-8") as f:
#         return json.load(f)

# def find_best_match(input_text: str, db_task: list[Dict], threshold: float = 50.0) -> Dict:
#     input_text = input_text.lower()
#     best_score = 0
#     best_task = None
#     for task in db_task:
#         task_desc = task["Description"].lower()
#         overlap = len(set(input_text.split()) & set(task_desc.split()))
#         score = overlap / max(len(task_desc.split()),1)
#         if score > best_score:
#             best_score = score
#             best_task = task
#     if best_score < threshold:
#         raise ValueError("No similar task found, YOU ARE USING THE ESTIMATION TOOL.")
#     return best_task


def estimation_tool(text: str) -> dict[str, float]:
    """
    Returns PERT based time estimates using nearest match from task DB
    """
#     task_db = load_data()
#     matched_task = find_best_match(text, task_db)

#     most_likely = matched_task["Estimation"]
#     optimistic = round(most_likely*0.7,2)
#     pessimistic = round(most_likely*1.5,2)
#     expected_time = calc_expected_time(optimistic, most_likely, pessimistic)
#     print(f"[MATCH] Matched to: {matched_task['TaskName']} (Estimation: {most_likely})")

    agent = AssistantAgent(
        name="Time Estimation Agent",
        system_message="You are an expert task planner, estimating task duration based on a description. ",
        llm_config=LLM_CONFIG,
    )

    estimation_prompt = f"""
    You are estimating the times in hours for a task from a description.


    Use the examples below to learn how effort scales with complexity, but DO NOT copy them blindly.

    Instead:
    - Extract the *patterns* in effort from the examples.
    - Compare the new tasks scope/complexity to those patterns.
    - Adjust your numbers accordingly.

    - Task: Create frontend components
        Complexity: High
        Optimistic: 358, MostLikely: 422, Pessimistic: 666
    - Task: Create environment
        Complexity: Easy
        Optimistic: 52, MostLikely: 102, Pessimistic: 207
    - Task: Set up Authentication
        Complexity: High
        Optimistic: 109, MostLikely: 219, Pessimistic: 333
    - Task: Creating database schema
        Complexity: High
        Optimistic: 231, MostLikely: 338, Pessimistic: 888
    - Task: API endpoints
        Complexity: Easy
        Optimistic: 62, MostLikely: 111, Pessimistic: 400

    Consider the complexity of the new task and estimate proportionally. You may go above or below these ranges if justified
    If the task is entirely unrelated, base your estimate on similar levels of complexity, scope, or effort.

    Be realistic. Do not invent extreme or random values.

    Do NOT invent or interpolate any other values under any circumstances.

    Be sure to:
    - Use the examples above to inform your estimation, not to limit it..
    - You may generalize, extrapolate, or interpolate based on task similarity, complexity, and scope.
    - Avoid extreme values unless the task clearly warrants it.
    - **Ensure your estimates are reasonable and justifiable in comparison to the examples**.

    The Description: {text}

   Return ONLY:

    - Optimistic: <number>
    - MostLikely: <number>
    - Pessimistic: <number>

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

