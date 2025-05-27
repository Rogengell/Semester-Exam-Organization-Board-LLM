import re
import json
from autogen import AssistantAgent, UserProxyAgent
from LLMExamAgents.config import LLM_CONFIG
from LLMExamAgents.tools.estimation_tool import estimation_tool
from LLMExamAgents.tools.calc_expected_time import calc_expected_time

OTHER_PROMPT = """
You are a project planning assistant.

1. Break down the given project component into smaller tasks, only do this step once.
2. Use the `estimation_tool` tool on each smaller tasks, only do this step once.
3. Use the `calc_expected_time` tool on each smaller tasks, using the output from `estimation_tool` tool, no other numbers are allowed to be used or replaced, only do this step once.
4. Use this output format for each smaller tasks:
[
  {{
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": float,
    "MostLikely": float,
    "Pessimistic": float,
    "ExpectedTime": float
  }},
  {{
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": float,
    "MostLikely": float,
    "Pessimistic": float,
    "ExpectedTime": float
  }}
]
5. terminate the process

### Input Project Component Description:
{input}

"""

def check_termination(msg):
    content = msg.get("content", "").strip().upper().replace("<", "").replace(">", "")
    print(f"Checking termination on message: {repr(content)}")
    return content == "TERMINATE"

def create_task_creator_agent() -> AssistantAgent:
    agent = AssistantAgent(
        name="TaskCreatorAgent",
        system_message= "You are a helpful ai assistant"
                        "You can break down project descriptions into smaller, meaningful tasks."
                        "You can read the data from the estimation_tool tool, it will return a dictionary of Optimistic, MostLikely and Pessimistic."
                        "Given the data from estimation_tool tool, you can use calc_expected_time tool to calculate the ExpectedTime."
                        "Don't include any other text in your response."
                        "Respond with <TERMINATE> on its own line, do not explain or elaborate when task are shown in json format",
        llm_config=LLM_CONFIG,
        is_termination_msg=check_termination,
        code_execution_config={"allow_code_execution": True},
    )
    agent.register_for_llm(name="estimation_tool", description="Estimate task durations based on examples")(estimation_tool)
    agent.register_for_llm(name="calc_expected_time", description="Calculate expected time from estimates")(calc_expected_time)
    return agent

def create_user_proxy() -> UserProxyAgent:
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=check_termination,
        human_input_mode="NEVER",
    )

    user_proxy.register_for_execution(name="calc_expected_time")(calc_expected_time)
    user_proxy.register_for_execution(name="estimation_tool")(estimation_tool)
    return user_proxy

def extract_json_tasks(history):
    # use a set to avoid duplicates
    unique_tasks = set() 
    # Initialize an empty list to store all tasks
    all_tasks = []

    for message in history:
        # check if message is a dictionary and has 'content'
        if isinstance(message, dict) and "content" in message:
            content = message["content"].strip()
            # Skip empty messages or those that contain only "TERMINATE"
            if not content or content.strip().upper() == "TERMINATE":
                continue

            try:
                # Find all JSON arrays of objects in the string
                json_str_matches = re.findall(r'\[\s*{.*?}\s*\]', content, re.DOTALL)
                for match in json_str_matches:
                    parsed = json.loads(match)
                    if isinstance(parsed, list):
                        # Filter tasks that may not have the expected keys
                        valid_tasks = [
                            task for task in parsed
                            if task.get("TaskName") and task.get("Description")
                        ]
                        for task in valid_tasks:
                            # Convert the dictionary to a hashable tuple, sorting items for consistency
                            # Sortiere die Items, um Konsistenz für das Hashing zu gewährleisten
                            task_tuple = tuple(sorted(task.items()))
                            unique_tasks.add(task_tuple)
            except json.JSONDecodeError as e:
                print(f"JSON-Dekodierungsfehler: {e} in Inhalt: '{content}'")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue

    # Convert the tuples in the set back to dictionaries
    for task_tuple in unique_tasks:
        all_tasks.append(dict(task_tuple))

    # Wrap the list in a dictionary with the key "tasks"
    # this ensures the output matches the expected JSON format
    return all_tasks
    
async def generate_tasks_from_description(description: str):
    user_proxy = create_user_proxy()
    task_creator_agent = create_task_creator_agent()

    user_proxy.initiate_chat(
        task_creator_agent,
        message=OTHER_PROMPT.format(input=description)
    )

    history = task_creator_agent.chat_messages.get(user_proxy, [])
    if not history:
        return []
    
    #print("History: ", str(history))

    tasks = extract_json_tasks(history)

    print("Tasks: "+ str(tasks))

    return tasks