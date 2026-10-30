import os
from dotenv import load_dotenv
import requests
import json
import time
import uuid

load_dotenv()
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("API_VERSION")
sora_deployment_name = os.getenv("SORA_DEPLOYMENT_NAME")

# Ensure trailing slash
if azure_openai_endpoint and not azure_openai_endpoint.endswith("/"):
    azure_openai_endpoint += "/"

params = f"?api-version={api_version}"
create_url = f"{azure_openai_endpoint}openai/v1/videos{params}"

headers = {
    "api-key": azure_openai_api_key,
    "Content-Type": "application/json",
}

# New Sora API: seconds must be "4", "8", or "12"; size one of
# "720x1280", "1280x720", "1024x1792", "1792x1024"
body = {
    "prompt": "Two futuristic robot musicians riding a glowing spaceship through colorful nebulae in deep space, cinematic, no logos",
    "seconds": "4",
    "size": "1280x720",
    "model": sora_deployment_name,
}

job_response = requests.post(create_url, headers=headers, json=body)
if not job_response.ok:
    print("❌ Video generation failed.")
    print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(",", ": ")))
else:
    print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(",", ": ")))
    job = job_response.json()
    job_id = job.get("id")
    status = job.get("status")
    status_url = f"{azure_openai_endpoint}openai/v1/videos/{job_id}{params}"

    print(f"⏳ Polling job status for ID: {job_id}")
    while status not in ["completed", "failed"]:
        time.sleep(5)
        job = requests.get(status_url, headers=headers).json()
        status = job.get("status")
        print(f"Status: {status} ({job.get('progress', 0)}%)")

    if status == "completed":
        print(job)
        print("✅ Video generation succeeded.")
        video_url = f"{azure_openai_endpoint}openai/v1/videos/{job_id}/content{params}"
        video_response = requests.get(video_url, headers=headers)
        if video_response.ok:
            output_filename = "output" + str(uuid.uuid4()) + ".mp4"
            with open(output_filename, "wb") as file:
                file.write(video_response.content)
            print(f'Generated video saved as "{output_filename}"')
        else:
            print("❌ Failed to download video content.")
            print(video_response.text)
    elif status == "failed":
        print("❌ Video generation failed.")
        print(json.dumps(job, sort_keys=True, indent=4, separators=(",", ": ")))
