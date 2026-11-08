import socket
import boto3
import uuid
import time

AWS_REGION = 'ap-southeast-2' 
TABLE_NAME = "ConfidentialAuditLog"
LOG_GROUP = "/acft/enclave-vault"
LOG_STREAM = "audit-stream"

kms = boto3.client('kms', region_name=AWS_REGION)
dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)
sts = boto3.client('sts', region_name=AWS_REGION)
logs = boto3.client('logs', region_name=AWS_REGION)

account_id = sts.get_caller_identity()["Account"]
SNS_TOPIC_ARN = f"arn:aws:sns:{AWS_REGION}:{account_id}:EnclaveAlerts"

# Create CloudWatch Log Group and Stream if they don't exist
try:
    logs.create_log_group(logGroupName=LOG_GROUP)
except logs.exceptions.ResourceAlreadyExistsException:
    pass
try:
    logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
except logs.exceptions.ResourceAlreadyExistsException:
    pass

# Custom logging function
def log_cw(message):
    print(message)
    timestamp = int(round(time.time() * 1000))
    logs.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=LOG_STREAM,
        logEvents=[{'timestamp': timestamp, 'message': message}]
    )

def process_in_vault(encrypted_data):
    log_cw("\n[VAULT] Receiving data... isolating memory.")
    
    log_cw("[VAULT] Requesting KMS decryption...")
    decrypted = kms.decrypt(CiphertextBlob=encrypted_data)['Plaintext'].decode('utf-8')
    
    log_cw("[VAULT] Data decrypted in isolated RAM. Anonymizing...")
    anonymized = f"REDACTED_RECORD_ID_****{decrypted[-4:]}"
    
    record_id = str(uuid.uuid4())
    log_cw(f"[VAULT] Writing sanitized result to DynamoDB (RecordID: {record_id})...")
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'RecordID': {'S': record_id},
            'Status': {'S': 'Processed securely in Vault'},
            'SanitizedData': {'S': anonymized}
        }
    )
    
    log_cw("[VAULT] Sending Admin Email Alert via SNS...")
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="Enclave Processing Success",
        Message=f"Vault successfully processed the record.\nRecordID: {record_id}\nSanitized Output: {anonymized}"
    )
    
    return "SUCCESS: Logged to DynamoDB, Admin Alert Sent, and CloudWatch Audited."

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 5000))
    s.listen()
    print("[VAULT] Hardware Enclave Simulator running on port 5000...")

    while True:
        conn, addr = s.accept()
        encrypted_blob = conn.recv(2048)
        if encrypted_blob:
            result = process_in_vault(encrypted_blob)
            conn.sendall(result.encode('utf-8'))
        conn.close()

if __name__ == "__main__":
    main()