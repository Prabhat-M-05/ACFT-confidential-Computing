# Confidential Computing: Serverless Edge-to-Cloud Enclave Simulation

## 📌 Overview
This project is a functional, cloud-integrated simulation of an **AWS Nitro Enclave** Confidential Computing pipeline. Traditional cloud security protects data *at rest* and *in transit*, but leaves it vulnerable **in use** (in system RAM). This architecture solves the "Data-in-Use" vulnerability by physically and logically isolating sensitive processing.

Because true AWS Nitro Enclaves require dedicated, non-burstable EC2 instances (outside the AWS Free Tier), this project simulates the air-gapped `vsock` (Virtual Socket) boundary using local TCP sockets, while leveraging real AWS serverless services to enforce cryptographic identity, auditing, and storage.

## 🏗️ Architecture Flow

1. **Ingestion (Data-in-Transit):** An external payload is sent via REST API to **AWS API Gateway**, triggering a **AWS Lambda** function.
2. **Encryption (Data-at-Rest):** The Lambda function encrypts the payload instantly using **AWS KMS** and drops the binary `.dat` ciphertext into an **Amazon S3** bucket.
3. **The Untrusted Host:** The local Host script (`host.py`) acts as an untrusted EC2 instance. It fetches the encrypted payload from S3 but lacks the KMS permissions to decrypt it.
4. **The Air-Gapped Transfer:** The Host passes the ciphertext through a local TCP socket (`127.0.0.1:5000`) representing the Enclave boundary.
5. **The Secure Enclave (Data-in-Use):** The Vault script (`vault.py`) receives the data, authenticates to KMS, and decrypts the data purely in isolated memory. It sanitizes Personally Identifiable Information (PII).
6. **Observability & Alerting:** The Vault writes the sanitized output to **Amazon DynamoDB**, streams an immutable audit trail to **Amazon CloudWatch**, and fires a real-time admin email via **Amazon SNS**.

## 🚀 AWS Services Utilized
* **API Gateway & Lambda:** Serverless ingestion and edge encryption.
* **KMS (Key Management Service):** Cryptographic operations (encryption/decryption).
* **S3 (Simple Storage Service):** Secure storage for ciphertext.
* **DynamoDB:** NoSQL database for sanitized record storage.
* **CloudWatch Logs:** Immutable, real-time security audit streaming.
* **SNS (Simple Notification Service):** Event-driven email alerting.
* **IAM (Identity and Access Management):** Strict Least-Privilege access control.

## 🛠️ Prerequisites
* **Python 3.x**
* **AWS Account** with an IAM User configured for programmatic access (Access Key ID & Secret Access Key).
* The IAM User must have permissions for KMS, S3, DynamoDB, SNS, and CloudWatch Logs.
* AWS CLI configured locally (`aws configure`).

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/enclave-project.git
   cd enclave-project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install boto3 requests
   ```

4. **Update Configuration Variables:**
   * Open `host.py` and replace `API_URL` with your actual AWS API Gateway endpoint.
   * Ensure the `AWS_REGION`, `S3_BUCKET`, and DynamoDB `TABLE_NAME` match your AWS environment.

## 🏃‍♂️ Running the Simulation

The simulation requires two separate terminal windows to represent the isolated environments.

**Terminal 1: Start the Secure Enclave Vault**
```bash
source venv/bin/activate
python3 vault.py
```
*(The vault is now listening on port 5000 for encrypted payloads)*

**Terminal 2: Trigger the Untrusted Host**
```bash
source venv/bin/activate
python3 host.py
```

### Expected Output:
1. Terminal 2 (`host.py`) will hit the API Gateway, download the resulting S3 file, and send it to the socket.
2. Terminal 1 (`vault.py`) will receive the file, process it, and output the CloudWatch audit logs.
3. You will receive an automated SNS email confirming the successful sanitization of the record.
4. The DynamoDB table will reflect the newly inserted, anonymized record.

## ⚠️ Security Notice
Do not hardcode AWS IAM Access Keys into the Python scripts. Always use `aws configure` or environment variables. Ensure you deactivate/delete your IAM Access Keys after testing to prevent unauthorized account access.

## 📄 License
This project was developed as part of an Advanced Cloud & Research Trends academic project. Feel free to use and modify it for educational purposes.