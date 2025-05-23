import json
from autogen import AssistantAgent, ConversableAgent, UserProxyAgent
from LLMExamAgents.config import LLM_CONFIG

TASK_BREAKDOWN_PROMPT = """
You are a project planning assistant.

1. You will be given a project component description. Break it down into tasks.

2. For each task:
- Estimate three time values: Optimistic (O), Most Likely (M), and Pessimistic (P) in hours.
- Use the tool `calculate_pert` to compute the expected time with the formula (O + 4M + P) / 6.

3. Return your answer in the format:

[
  {{
    "TaskName": "...",
    "Description": "...",
    "Optimistic": 2,
    "MostLikely": 4,
    "Pessimistic": 6,
    "ExpectedTime": 4.0
  }},
  {{
    "TaskName": "...",
    "Description": "...",
    "Optimistic": 3,
    "MostLikely": 5,
    "Pessimistic": 7,
    "ExpectedTime": 5.0
  }}
]

Project Component Description:
{input}

Respond only with the tasks. Do not terminate prematurely, always provide task details.
""" 



def create_task_creator_agent() -> AssistantAgent:
    return AssistantAgent(
        name="TaskCreatorAgent",
        system_message="You are a helpful assistant that breaks down project descriptions into tasks with time estimates.",
        llm_config=LLM_CONFIG,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content", ""),
        code_execution_config={"allow_code_execution": True},
    )

def create_user_proxy() -> UserProxyAgent:
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content", ""),
        human_input_mode="NEVER",
    )

    user_proxy.register_for_execution(name="calculate_pert")(calculate_pert)
    return user_proxy

def extract_json_tasks(response_content: str):
    try:
        # Strip extra whitespace and handle common formatting issues
        response_content = response_content.strip()

        # Look for JSON-like structure, assuming response is a valid list of tasks
        if response_content.startswith("[") and response_content.endswith("]"):
            task_json_str = response_content
        else:
            # Handle cases where there are extra characters (e.g., "TERMINATE" or other content)
            start = response_content.find("[")
            end = response_content.rfind("]") + 1
            task_json_str = response_content[start:end]

        # Parse the JSON and return the list of tasks
        tasks = json.loads(task_json_str)
        print(tasks)
        return tasks
    except Exception as e:
        print("Failed to parse JSON:", e)
        return []
    
def calculate_pert(optimistic: float, most_likely: float, pessimistic: float) -> float:
    return round((optimistic + 4 * most_likely + pessimistic) / 6, 2)

async def generate_tasks_from_description(description: str):
    user_proxy = create_user_proxy()
    task_creator_agent = create_task_creator_agent()
    print("before agent")
    user_proxy.initiate_chat(
        task_creator_agent,
        message=TASK_BREAKDOWN_PROMPT.format(input=description)
    )
    print("after agent")
    history = task_creator_agent.chat_messages.get(user_proxy, [])
    if not history:
        return None
    
    print(history)
    content = history[-1].get("content", "")
    print(content)
    return extract_json_tasks(content)