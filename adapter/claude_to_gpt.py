#!/usr/bin/env python
'''
@File    :   claude_to_gpt.py
@Time    :   2024/03/31 22:18:00
@Author  :   hongyu zhang
@Version :   1.0
@Desc    :   None
'''
import os
import time
import argparse
import json
import boto3
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from starlette.responses import StreamingResponse, Response


app = FastAPI()


# Convert OpenAI messages to Claude prompt
def convert_messages_to_prompt(messages):
    system = None
    converted_messages = []
    expect = "user"
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == expect == "user" and messages[i]["content"].strip() != "":
            converted_messages.append({"role": messages[i]["role"], "content": messages[i]["content"]})
            expect = "assistant"
        elif messages[i]["role"] == expect == "assistant" and messages[i]["content"].strip() != "" and \
            i - 1 >= 0 and messages[i - 1]["role"] == "user" and messages[i - 1]["content"].strip() != "":
            converted_messages.append({"role": messages[i]["role"], "content": messages[i]["content"]})
            expect = "user"
        elif messages[i]["role"] == "system":
            system = messages[i]["content"]
        else:
            continue
    converted_messages = converted_messages[::-1]
    return converted_messages, system


# Convert Claude messages to OpenAI messages
def openai_to_claude_params(openai_params):
    claude_params = {}

    claude_params["body"] = {}
    claude_params["body"]["anthropic_version"] = "bedrock-2023-05-31"
    claude_params["body"]["messages"], claude_params["body"]["system"] = convert_messages_to_prompt(openai_params["messages"])

    known_params = ["model", "messages", "max_tokens", "stop", "temperature", "stream"]
    for key in openai_params.keys():
        if key not in known_params:
            claude_params[key] = openai_params[key]

    if openai_params.get("max_tokens"):
        claude_params["body"]["max_tokens"] = openai_params["max_tokens"]
    else:
        claude_params["body"]["max_tokens"] = 1000

    if openai_params.get("stop"):
        claude_params["body"]["stop_sequences"] = openai_params.get("stop")

    if openai_params.get("temperature"):
        claude_params["body"]["temperature"] = openai_params.get("temperature")
    claude_params["body"] = json.dumps(claude_params["body"], ensure_ascii=False)

    claude_params["model"] = openai_params["model"]
    claude_params["stream"] = True if openai_params.get("stream") else False
    return claude_params


# Convert Claude response to OpenAI response
def claude_to_openai_params(response):
    claude_params = json.loads(response.get('body').read())        

    openai_params = {}

    known_params = ["id", "content", "model", "stop_reason", "usage"]
    for key in openai_params.keys():
        if key not in known_params:
            openai_params[key] = claude_params[key]

    openai_params["choices"] = []
    for content in claude_params["content"]:
        choice = {
            "message": {"role": "assistant", "content": content["text"]},
            "finish_reason": claude_params["stop_reason"],
            "index": 0,
            "content_filter_results": {
                "hate": {
                    "filtered": False,
                    "severity": "safe"
                },
                "self_harm": {
                    "filtered": False,
                    "severity": "safe"
                },
                "sexual": {
                    "filtered": False,
                    "severity": "safe"
                },
                "violence": {
                    "filtered": False,
                    "severity": "safe"
                }
            }
        }
        openai_params["choices"].append(choice)

    openai_params["usage"] = {"prompt_tokens": claude_params["usage"]["input_tokens"],
                                "completion_tokens": claude_params["usage"]["output_tokens"],
                                "total_tokens": claude_params["usage"]["input_tokens"] + claude_params["usage"]["output_tokens"],
                              }

    openai_params["id"] = claude_params["id"]
    openai_params["object"] = "chat.completion"
    openai_params["created"] = int(time.time())
    openai_params["system_fingerprint"] = claude_params["id"]
    return openai_params


# Convert Claude streaming api to OpenAI streaming api
def claude_to_openai_params_stream(claude_params):
    created = int(time.time())
    model = "claude"
    id = ""
    finish_reason = ""
    for event in claude_params.get("body"):
        chunk = json.loads(event["chunk"]["bytes"])

        if chunk['type'] == 'message_start':
            model = chunk["message"]["model"]
            id = chunk["message"]["id"]
            body = {
                "id": "",
                "object": "",
                "created": 0,
                "model": "",
                "prompt_filter_results": [{
                    "prompt_index": 0,
                    "content_filter_results": {
                        "hate": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "self_harm": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "sexual": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "violence": {
                            "filtered": False,
                            "severity": "safe"
                        }
                    }
                }],
                "choices": []
            }
            yield f"data: {json.dumps(body, ensure_ascii=False)}\n\n"

            body = {
                "id": id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "finish_reason": None,
                    "index": 0,
                    "delta": {
                        "role": "assistant"
                    },
                    "content_filter_results": {}
                }],
                "system_fingerprint": id
            }
            yield f"data: {json.dumps(body, ensure_ascii=False)}\n\n"

        if chunk['type'] == 'content_block_delta':
            body = {
                "id": id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "finish_reason": None,
                    "index": 0,
                    "delta": {
                        "content": chunk['delta']['text']
                    },
                    "content_filter_results": {
                        "hate": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "self_harm": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "sexual": {
                            "filtered": False,
                            "severity": "safe"
                        },
                        "violence": {
                            "filtered": False,
                            "severity": "safe"
                        }
                    }
                }],
                "system_fingerprint": id
            }
            yield f"data: {json.dumps(body, ensure_ascii=False)}\n\n"

        if chunk['type'] == 'message_delta':
            finish_reason = chunk['delta']['stop_reason']

        if chunk['type'] == 'message_stop':
            body = {
                "id": id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "finish_reason": finish_reason,
                    "index": 0,
                    "delta": {},
                    "content_filter_results": {}
                }],
                "system_fingerprint": id
            }
            yield f"data: {json.dumps(body, ensure_ascii=False)}\n\n"
            yield f"data: [DONE]\n\n"


# Claude to OpenAI adapter
@app.post("/v1/chat/completions")
async def handle_completions(openai_request: Request, authorization: str = Header(None)):
    openai_params = await openai_request.json()
    claude_params = openai_to_claude_params(openai_params)
    if args.api_key not in authorization:
        detail = {
            "error": {
                "message": f"Incorrect API key provided: {authorization}.",
                "type": "invalid_request_error",
                "param": None,
                "code": "invalid_api_key"
            }
        }
        raise HTTPException(status_code=400, detail=detail)

    if claude_params.get("stream", False):
        raw_response = bedrock.invoke_model_with_response_stream(modelId=claude_params["model"], body=claude_params["body"])
        status_code=raw_response["ResponseMetadata"]["HTTPStatusCode"]
        response_body = claude_to_openai_params_stream(raw_response)
        return StreamingResponse(content=response_body, status_code=status_code)
    else:
        raw_response = bedrock.invoke_model(modelId=claude_params["model"], body=claude_params["body"])
        status_code = raw_response["ResponseMetadata"]["HTTPStatusCode"]
        response_body = claude_to_openai_params(raw_response)
        return Response(content=json.dumps(response_body, ensure_ascii=False), status_code=status_code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--aws_access_key_id", type=str, default=os.getenv("AWS_ACCESS_KEY_ID"))
    parser.add_argument("--aws_secret_access_key", type=str, default=os.getenv("AWS_SECRET_ACCESS_KEY"))
    parser.add_argument("--region_name", type=str, default=os.getenv("REGION_NAME", "us-east-1"))
    parser.add_argument("--api_key", type=str, default=os.getenv("API_KEY", ""))
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=os.getenv("PORT", 80))

    args = parser.parse_args()

    bedrock = boto3.client(service_name='bedrock-runtime',
                            aws_access_key_id=args.aws_access_key_id,
                            aws_secret_access_key=args.aws_secret_access_key,
                            region_name=args.region_name,
                            )
    
    uvicorn.run(app,
                host=args.host,
                port=args.port,
                )
