#!/usr/bin/env python
from openai import OpenAI

client = OpenAI(api_key='this-key-can-be-customized',
                base_url='http://127.0.0.1:8080/v1')

completion = client.chat.completions.create(
  model="anthropic.claude-v2",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ]
)

print(completion.choices[0].message)