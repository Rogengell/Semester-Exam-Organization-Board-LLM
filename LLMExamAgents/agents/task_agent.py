import json
from autogen import AssistantAgent, ConversableAgent
from LLMExamAgents.config import LLM_CONFIG

TASK_BREAKDOWN_PROMPT = """
You are a project planning assistant.

You will be given a project component description. Break it down into tasks.

For each task:
- Estimate three time values: Optimistic (O), Most Likely (M), and Pessimistic (P) in hours.
- Use the tool `calculate_pert` to compute the expected time with the formula (O + 4M + P) / 6.

Return your answer in the format:

[
  {{
    "TaskName": "...",
    "Description": "...",
    "Optimistic": 2,
    "MostLikely": 4,
    "Pessimistic": 6,
    "ExpectedTime": "<result from calling calculate_pert>"
  }}
]

Project Component Description:
{input}

Respond with TERMINATE.
"""

def create_task_creator_agent() -> ConversableAgent:
    return ConversableAgent(
        name="TaskCreatorAgent",
        system_message="You are a helpful assistant that breaks down project descriptions into tasks with time estimates.",
        llm_config=LLM_CONFIG,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        code_execution_config={"allow_code_execution": True}  # if needed
    )

def create_user_proxy() -> ConversableAgent:
    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode=False
    )

    user_proxy.register_for_execution(name="calculate_pert")(calculate_pert)
    return user_proxy

def extract_json_tasks(response_content: str):
    try:
        start = response_content.find("[")
        end = response_content.rfind("]") + 1
        task_json_str = response_content[start:end]
        return json.loads(task_json_str)
    except Exception as e:
        print("Failed to parse JSON:", e)
        return []
    
def calculate_pert(optimistic: float, most_likely: float, pessimistic: float) -> float:
    return round((optimistic + 4 * most_likely + pessimistic) / 6, 2)

async def generate_tasks_from_description(description: str):
    user_proxy = create_user_proxy()
    task_creator_agent = create_task_creator_agent()

    await user_proxy.initiate_chat(
        task_creator_agent,
        message=TASK_BREAKDOWN_PROMPT.format(input=description)
    )

    history = task_creator_agent.chat_messages.get(user_proxy, [])
    if not history:
        return None

    content = history[-1].get("content", "")
    return extract_json_tasks(content)
