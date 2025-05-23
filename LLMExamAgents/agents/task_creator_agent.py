import json
from autogen import AssistantAgent, ConversableAgent
from LLMExamAgents.config import LLM_CONFIG
import os


Search_prompt = """
Use the parameters below to search using the API Endpoint described within '???'.

Parameters: {input}

Once you've created the results, display the results and reply with TERMINATE.
"""

def create_task_creator_agent() -> ConversableAgent:
    # define the agent
    agent = ConversableAgent(
        name="Task Creator",
        system_message="""
        You are a creator of tasks based on project description assistant.

        1. Prompt the human to provide the following parameters: 
            - Description of Task

        You may ask follow-up questions to clarify incomplete or ambigous input.
        """,
        llm_config=LLM_CONFIG,
    )


def create_user_proxy():
    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
    )
    # user_proxy.register_for_execution(name="query_handling")(query_handling)
    # user_proxy.register_for_execution(name="print_papers")(print_papers)
    return user_proxy

def serialize_message(message):
        return{
                "Task Name": message.get("TaskName"),
                "Task Short Description": message.get("Description"),
                "Task Time": message.get("TaskTime"),
                "content": message.get("content"),
        }

def main():
    user_proxy = create_user_proxy()
    TaskCreator_agent = create_task_creator_agent()
    # Getting user input
    description = input("Enter the Description of the Project: ")

    # Send user input to the agent as dynamic prompt
    user_input = f"Description: {description}"

    user_proxy.initiate_chat(
        TaskCreator_agent, 
        message=Search_prompt.format(input=user_input)
    )

    history = TaskCreator_agent.chat_messages.get(user_proxy, [])
    serialized_history = [serialize_message(m) for m in history]

    save_path = os.path.join(os.getcwd(), "list_of_tasks.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(serialized_history, f, indent=2, ensure_ascii=False)
    print("Full convo saved to list_of_tasks.json")

if __name__ == "__main__":
    main()