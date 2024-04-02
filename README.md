# AWS Claude to OpenAI GPT
- This project converts the API of AWS's Claude model to the OpenAI Chat API format.

## Run in Docker Environment
### Build Docker Image
```shell
git clone https://github.com/moonpath/claude-to-gpt.git
cd claude-to-gpt
sudo docker build -t claude-to-gpt:latest -f Dockerfile .
```

### Run Docker Container
```shell
sudo docker run -itd -p 8080:80 \
-e AWS_ACCESS_KEY_ID='your-aws-access-key-id' \
-e AWS_SECRET_ACCESS_KEY='your-aws-secret-access-key' \
-e REGION_NAME='us-east-1' \
-e HOST='0.0.0.0' \
-e PORT=80 \
-e API_KEY='this-key-can-be-customized' \
claude-to-gpt:latest
```

## Run in Python Environment
### Install Python Package
```shell
git clone https://github.com/moonpath/claude-to-gpt.git
cd claude-to-gpt
pip install -r requirements.txt
```

### Run Python Script
```shell
python adapter/claude_to_gpt.py \
--aws_access_key_id='your-aws-access-key-id' \
--aws_secret_access_key='your-aws-secret-access-key' \
--region_name='us-east-1' \
--host='0.0.0.0' \
--port=8080 \
--api_key='this-key-can-be-customized' \
```

## Usage Examples
```shell
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer this-key-can-be-customized" \
  -d '{
    "model": "anthropic.claude-v2",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```
```python
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
```
