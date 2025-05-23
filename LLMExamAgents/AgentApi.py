from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.task_agent import generate_tasks_from_description
import uvicorn
import json
import os


# Define input schema
class UserStoryInput(BaseModel):
    story: str

# Initialize FastAPI
app = FastAPI()

@app.post("/AgentTaskGeneration")
async def analyze_story(input: UserStoryInput):
    # Trim input
    story = input.story

    # TODO: Agent Call Here
    tasks = await generate_tasks_from_description(story)
    if not tasks:
        raise HTTPException(status_code=500, detail="Agent failed to generate tasks.")
    
    return {"tasks": tasks}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, timeout_keep_alive=120, timeout=300)