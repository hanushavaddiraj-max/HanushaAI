import azure.functions as func
import logging
import os 
import json
import azure.identity
from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy, BinaryBase64DecodePolicy

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="inputqueue",
                               connection="STORAGE_CONNECTION") 
def GreetingByBatman(msg: func.QueueMessage) -> None:
    logging.info('Python queue trigger function processed a queue item')

    # Queue to send message to
    queue_client = QueueClient(
        os.environ["STORAGE_CONNECTION__queueServiceUri"],
        queue_name="outputqueue",
        credential=DefaultAzureCredential(),
        message_encode_policy=BinaryBase64EncodePolicy(),
        message_decode_policy=BinaryBase64DecodePolicy()
    )

    messagepayload = json.loads(msg.get_body().decode('utf-8'))
    name=messagepayload["name"]

    death_note = f""" It's not who you are underneath, {name}, but what you do that defines you. Stay strong, stay vigilant… and happy to have you here """ 

    result_message = {
        'Value': death_note
    }

    queue_client.send_message(json.dumps(result_message).encode('utf-8'))

    logging.info(f"Sent message to queue with message {result_message}")
