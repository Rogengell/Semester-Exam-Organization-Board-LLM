import re
import json
from autogen import AssistantAgent, ConversableAgent, UserProxyAgent
from LLMExamAgents.config import LLM_CONFIG

TASK_BREAKDOWN_PROMPT = """
You are a project planning assistant.

You will be given a project component description. Break it down into tasks.

You have access to reference historical estimations for similar tasks: {reference_estimations}

Use this reference to make informed guesses about time estimates. If a task seems similar to a past one, consider using a similar estimate.

For each task:
- Estimate three time estimates for the task: Optimistic (O), MostLikely (M), and Pessimistic (P) in hours.
- Use the tool `calculate_pert` to compute the expected time with the mathematics formula ((Optimistic + (4*MostLikely) + Pessimistic) / 6).

Return your answer in the format:

[
  {{
    "TaskName": "",
    "Description": "",
    "Optimistic": 2,
    "MostLikely": 4,
    "Pessimistic": 6,
    "ExpectedTime": 4.0
  }},
  {{
    ...
  }}
]

Project Component Description:
{input}

Respond only with the tasks. Do not terminate prematurely, always provide task details.
Do not provide breakdown, only tasks, in the provided format.
If user does not provide feedback, any output or is empty, determine if more task are needed else respond with "terminate" in uppercase.
After a maximum of 2 iterations respond with "terminate" in uppercase.
""" 
def load_data(filepath="db_tasks.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        history = json.load(f)
    return history

# Load and prep of reference data
def load_reference_estiations(filepath="db_tasks.json"):
    reference_data = load_data(filepath)
    formatted = [
        f"{item['TaskName']}: {item['Description']} (Estimation: {item['Estimation']}h)"
        for item in reference_data
    ]
    return "\n".join(formatted)

def create_task_creator_agent() -> AssistantAgent:
    return AssistantAgent(
        name="TaskCreatorAgent",
        system_message="You are a helpful assistant that breaks down project descriptions into tasks with time estimates.",
        llm_config=LLM_CONFIG,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content"),
        code_execution_config={"allow_code_execution": True},
    )

def create_user_proxy() -> UserProxyAgent:
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content"),
        human_input_mode="NEVER",
    )

    user_proxy.register_for_execution(name="calculate_pert")(calculate_pert)
    return user_proxy

def extract_json_tasks(history):
    all_tasks = []

    for message in history:
        if isinstance(message, dict) and "content" in message:
            content = message["content"].strip()
            if not content or content.strip().upper() == "TERMINATE":
                continue

            try:
                json_str_matches = re.findall(r'\[\s*{.*?}\s*\]', content, re.DOTALL)
                for match in json_str_matches:
                    parsed = json.loads(match)
                    if isinstance(parsed, list):
                        valid_tasks = [
                            task for task in parsed
                            if task.get("TaskName") and task.get("Description")
                        ]
                        all_tasks.extend(valid_tasks)
            except Exception as e:
                print("Failed to parse content:", e)
                continue

    return all_tasks
    
def calculate_pert(optimistic: float, most_likely: float, pessimistic: float) -> float:
    return round((optimistic + 4 * most_likely + pessimistic) / 6, 2)

async def generate_tasks_from_description(description: str):
    user_proxy = create_user_proxy()
    task_creator_agent = create_task_creator_agent()
    reference_estimations = load_reference_estiations()
    full_prompt = TASK_BREAKDOWN_PROMPT.format(input=description, reference_estimations=reference_estimations)

    user_proxy.initiate_chat(
        task_creator_agent,
        message=full_prompt
    )

    history = task_creator_agent.chat_messages.get(user_proxy, [])
    if not history:
        return []
    
    print("History: ", str(history))

    tasks = extract_json_tasks(history)

    print("Tasks: "+ str(tasks))

    return tasks