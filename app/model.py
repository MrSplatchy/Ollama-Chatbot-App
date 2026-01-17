from ollama import chat
from dotenv import load_dotenv
from os import getenv

load_dotenv()
model = getenv("MODEL")

async def generateResponse(content, chat_history: list): 
    # LLM Preparations
    response = chat(
        model = model,
        messages=chat_history,
        stream=True,

    )
    llm_response = "" 

    # Stream the response and prepare it to be added to the chat history
    for chunk in response:
        content = chunk['message']['content']
        if content:
            llm_response += content
            yield content


    chat_history.append({"role": "assistant", "content": llm_response})




