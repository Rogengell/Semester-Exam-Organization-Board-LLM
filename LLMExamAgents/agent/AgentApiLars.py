from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from task_creator_agent import generate_tasks_from_description
import json
from autogen import AssistantAgent

# Define input schema
class UserStoryInput(BaseModel):
    story: str

# Initialize FastAPI
app = FastAPI()

@app.post("/AgentTaskGeneration")
async def analyze_story(input: UserStoryInput):
    # Trim input
    story = input.story.strip()

    # TODO: Agent Call Here
    try:
        tasks = test()
        #tasks = generate_tasks_from_description(story)
        return JSONResponse(content={"tasks": tasks}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=200)

    # return {
    #     "user_story": story,
    #     "analysis_result": "access"
    # }

def test() -> AssistantAgent:
    agent = AssistantAgent(
        human_input_mode="NEVER",
    )
    agent.register_for_llm(name="generate_tasks_from_description", description="Contains details on how to generate tasks")(generate_tasks_from_description)
    return agent


if __name__ == "__main__":
    test()
    uvicorn.run(app, host="0.0.0.0", port=8008)
