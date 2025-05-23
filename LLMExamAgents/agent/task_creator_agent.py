import json
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from LLMExamAgents.config import LLM_CONFIG


Create_prompt = """
You are a helpful assistant tasked with creating a task breakdown from a project description.

Given the following project description:
"{input}"

Generate a list of tasks. Each task must:
- Take no more than 4 hours for an average developer.
- Have the following fields:
  - "TaskName"
  - "Description"
  - "TaskTime" (in hours, max 4)

Return the result as a JSON array of task dictionaries.
Once you're done, say 'TERMINATE'.
"""

def create_task_creator_agent() -> AssistantAgent:
    # define the agent
    return AssistantAgent(
        name="TaskGenerationAgent",
        system_message="""
        You are a creator of tasks based on project descriptions.
        Given a project description, break it down into tasks of ≤4 hours.
        Each task should include:
        - Task Name
        - Task Short Description
        - Task Time (in hours)
        """,
        llm_config=LLM_CONFIG,
    )


def create_user_proxy():
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    )
    return user_proxy

def serialize_message(message):
    try:
        # If content contains a JSON string, parse it
        content = message.get("content", "")
        if content.strip().startswith("[") and content.strip().endswith("]"):
            return json.loads(content)
        return{
            "TaskName": message.get("TaskName"),
            "Description": message.get("Description"),
            "TaskTime": message.get("TaskTime"),
        }
    except Exception:
        return {"raw_message": message}

def generate_tasks_from_description(description: str):
    user_proxy = create_user_proxy()
    TaskCreator_agent = create_task_creator_agent()

    # Send user input to the agent as dynamic prompt
    user_input = f"{description}"

    user_proxy.initiate_chat(
        TaskCreator_agent, 
        message=Create_prompt.format(input=user_input)
    )

    history = TaskCreator_agent.chat_messages.get(user_proxy, [])
    serialized_history = [serialize_message(m) for m in history]

    return serialized_history

# Fix constructor?

    # save_path = os.path.join(os.getcwd(), "list_of_tasks.json")
    # with open(save_path, "w", encoding="utf-8") as f:
    #     json.dump(serialized_history, f, indent=2, ensure_ascii=False)
    # print("Full list saved to list_of_tasks.json")

# if __name__ == "__main__":
#     generate_tasks_from_description()