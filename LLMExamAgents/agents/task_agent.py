import re
import json
from autogen import AssistantAgent, UserProxyAgent
from LLMExamAgents.config import LLM_CONFIG
from LLMExamAgents.tools.estimation_tool import estimation_tool
from LLMExamAgents.tools.calc_expected_time import calc_expected_time

OTHER_PROMPT = "Input Project Component Description:\n{input}"

SYSTEM_MESSAGE = """
You are a project planning assistant.

IMPORTANT RULES (you must obey them):
1. Do NOT use or attempt to call a tool named 'break_down_project' — it does NOT exist.
2. You MUST break down the input project component yourself, step by step.
3. For each smaller task, call 'estimation_tool' ONCE and wait for the result.
4. Then pass the returned result (without changing anything) to 'calc_expected_time'.
5. NEVER make up any numbers or durations yourself.
6. Use the exact result from estimation_tool for calc_expected_time.

OUTPUT FORMAT:
Return a JSON array of tasks, like this:
[
  {
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": float,
    "MostLikely": float,
    "Pessimistic": float,
    "ExpectedTime": float
  },
  {
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": float,
    "MostLikely": float,
    "Pessimistic": float,
    "ExpectedTime": float
  }
]

After the full output, respond on a new line with exactly:
<TERMINATE>

Do not include any explanation or text after <TERMINATE>.
"""

def check_termination(msg):
    content = msg.get("content", "")

    # Extract all JSON-like blocks using regex (non-greedy)
    potential_blocks = re.findall(r'\[[\s\S]*?\]', content)

    # Remove only those blocks that are valid JSON lists of dicts
    for block in potential_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                content = content.replace(block, "")
        except Exception:
            # If malformed, ignore removal, keep content as is
            pass

    # Now just check if "TERMINATE" is anywhere in remaining content (case-insensitive)
    if "TERMINATE" in content.upper():
        print(f"Termination found in content after removing JSON blocks.")
        return True

    print(f"No termination found. Remaining content: {repr(content)}")
    return False

def create_task_creator_agent() -> AssistantAgent:
    agent = AssistantAgent(
        name="TaskCreatorAgent",
        system_message= SYSTEM_MESSAGE,
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