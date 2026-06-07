from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI()

def askllm(messages: list):    
    response = client.chat.completions.create(
        model= "gpt-4o-mini",
        temperature= 0.6,
        messages= messages
    )
    return response.choices[0].message.content
