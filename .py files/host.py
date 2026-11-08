import socket
import boto3
import requests
import time

# PASTE YOUR LAMBDA API GATEWAY URL HERE:
API_URL = "https://r28m7drar0.execute-api.ap-southeast-2.amazonaws.com/default/EnclaveIngestAPI"

AWS_REGION = 'ap-southeast-2'
S3_BUCKET = "confidential-input-bucket-acft"
s3 = boto3.client('s3', region_name=AWS_REGION)

def main():
    print("1. Sending raw sensitive data to Serverless API Gateway...")
    payload = {"medical_record": "HIGHLY_CONFIDENTIAL_DIAGNOSIS_#7742"}
    
    # Hit the external cloud API
    response = requests.post(API_URL, json=payload)
    
    if response.status_code != 200:
        print(f"API Error: {response.text}")
        return
        
    api_response = response.json()
    file_name = api_response.get('s3_file_key')
    
    print(f"2. Lambda encrypted the data and stored it in S3 as: {file_name}")
    time.sleep(2) # Brief pause for S3 consistency
    
    print("3. Fetching encrypted data from S3 to pass to Vault...")
    s3_response = s3.get_object(Bucket=S3_BUCKET, Key=file_name)
    downloaded_blob = s3_response['Body'].read()
    
    print("4. Sending encrypted data to Enclave Vault via local socket...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.sendall(downloaded_blob)
    
    result = s.recv(1024).decode('utf-8')
    print(f"\n[HOST] Final Response from Vault: {result}")
    s.close()

if __name__ == "__main__":
    main()