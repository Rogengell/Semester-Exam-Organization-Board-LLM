import re
import json
from autogen import AssistantAgent, UserProxyAgent
from LLMExamAgents.config import LLM_CONFIG
from LLMExamAgents.tools.estimation_tool import estimation_tool
from LLMExamAgents.tools.calc_expected_time import calc_expected_time

TASK_BREAKDOWN_PROMPT = """
You are a project planning assistant.

Your task is to break down a given project component into smaller tasks and provide two sets of different time estimations for each task:

1. **First Estimate (Answer 1)**:
   - Break down the project using your own logic.
   - For each task, estimate the time using:
     - Optimistic (O)
     - Most Likely (M)
     - Pessimistic (P)
   - Compute Expected Time using the tool `calc_expected_time`.
   - Label this as "Answer": "1".

2. **Second Estimate (Answer 2)**:
   - After generating the first estimate(Answer 1), create a **new task estimate**(Answer 2).
   - Call the `estimation_tool` tool with the task description.
   - Use the returned values (Optimistic, MostLikely, Pessimistic) **exactly as provided**.
   - Compute Expected Time using the tool `calc_expected_time`.
   - **Do not overwrite or reuse Answer 1 data.**
   - If the `estimation_tool` tool returns terminate, skip that task in answer 2.
   - Label this as "Answer": "2".
   - Answer 2 must be a separate object with its own values.

### Output Format:
Return both estimations in the following format (one object per estimation):

[
  {{
    "Answer": "1",
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": int,
    "MostLikely": int,
    "Pessimistic": int,
    "ExpectedTime": int
  }},
  {{
    "Answer": "2",
    "TaskName": "Name of task",
    "Description": "Brief description",
    "Optimistic": int,
    "MostLikely": int,
    "Pessimistic": int,
    "ExpectedTime": int
  }}
]

### Rules:
- Output only the list of task dictionaries in the above format.
- Do not include explanations, headings, comments or summaries.
- Use the output from the `estimation_tool` exactly as returned. Do not modify the values.
- If the input is empty or unclear, or if this is a follow-up with no additional user feedback, respond with "terminate" in uppercase.
- After a maximum of one iteration with no user feedback, respond with "terminate" in uppercase.

### Input Project Component Description:
{input}
""" 



def create_task_creator_agent() -> AssistantAgent:
    agent = AssistantAgent(
        name="TaskCreatorAgent",
        system_message="You are a helpful assistant that breaks down project descriptions into tasks with time estimates.",
        llm_config=LLM_CONFIG,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content"),
        code_execution_config={"allow_code_execution": True},
    )
    agent.register_for_llm(name="estimation_tool", description="Estimate task durations based on examples")(estimation_tool)
    agent.register_for_llm(name="calc_expected_time", description="Calculate expected time from estimates")(calc_expected_time)
    return agent

def create_user_proxy() -> UserProxyAgent:
    user_proxy = UserProxyAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg.get("content"),
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
        message=TASK_BREAKDOWN_PROMPT.format(input=description)
    )

    history = task_creator_agent.chat_messages.get(user_proxy, [])
    if not history:
        return []
    
    print("History: ", str(history))

    tasks = extract_json_tasks(history)

    print("Tasks: "+ str(tasks))

    return tasks