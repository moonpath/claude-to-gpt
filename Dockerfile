FROM python:3.10 as base

# Required environment variables
ENV AWS_ACCESS_KEY_ID=''
ENV AWS_SECRET_ACCESS_KEY=''
ENV REGION_NAME='us-east-1'

# Optional environment variables
ENV API_KEY=''
ENV HOST='0.0.0.0'
ENV PORT=80

RUN pip install \
    boto3 \
    fastapi \
    uvicorn

COPY adapter/claude_to_gpt.py /app/claude_to_gpt.py
RUN chmod +x /app/claude_to_gpt.py

WORKDIR "/app"
EXPOSE $PORT
ENTRYPOINT ["/app/claude_to_gpt.py"]