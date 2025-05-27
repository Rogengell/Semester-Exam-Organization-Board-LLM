# Semester-Exam Organization-Board

Exam for Machine-Learning

# Setup

## Install all packages

```bash
pip install -r requirements.txt
```

## Download Model

in this project we are using a local model from Ollama, we recommending to download the llama3.1:8b model. If you prefer an other model
than you have to change the config file, but the model ist tested based on the recommended model. How to download model:
```bash
ollama run llama3.1:8b
```
when the model is downloaded and installed you can go on with the next section

## Compose docker

```bash
docker-compose up --build agent-python
```

# Testing the Ai Agent in Postman

Once docker has been composed, open Postman desktop and create a new post request to this endpoint

```bash
http://localhost:8080/AgentTaskGeneration
```

## Steps

1. click on body and create a json like this

´´´
{
"story":"I want to build an TODO APP"
}
´´´ 2. then send the request and wait 3-5 min depending on the complexity
