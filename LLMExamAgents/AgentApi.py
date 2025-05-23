from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

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

    return {
        "user_story": story,
        "analysis_result": "access"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
