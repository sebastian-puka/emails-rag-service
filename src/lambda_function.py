import boto3
import json
import time
import os

# ---------- Configuration ----------
REGION = os.environ.get("AWS_REGION", "us-east-1")
VECTOR_BUCKET = os.environ.get("VECTOR_BUCKET", "email-test")
INDEX_NAME = os.environ.get("INDEX_NAME", "notifications")

# ---------- AWS Clients (reuse across invocations) ----------
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)


def lambda_handler(event, context):
    """
    Lambda entry point
    """

    # ---------- 1. Read input parameters ----------
    try:
        email_subject = event["email_subject"]
        email_body = event["email_body"]
        user_email = event["user_email"]
        zone = event["zone"]
        package_code = event["package_code"]
    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Missing required parameter: {str(e)}"
            })
        }

    # ---------- 2. Generate unique vector key ----------
    vector_key = f"email_{int(time.time())}"

    # ---------- 3. Prepare embedding text ----------
    embedding_text = f"""
    Email notification about a package delivery.
    User email: {user_email}
    Subject: {email_subject}
    Message: {email_body}
    """

    # ---------- 4. Generate embedding ----------
    try:
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": embedding_text})
        )

        response_body = json.loads(response["body"].read())
        embedding = response_body["embedding"]

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to generate embedding",
                "details": str(e)
            })
        }

    # ---------- 5. Store vector in S3 Vectors ----------
    try:
        s3vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            vectors=[
                {
                    "key": vector_key,
                    "data": {"float32": embedding},
                    "metadata": {
                        "user_email": user_email,
                        "subject": email_subject,
                        "zone": zone,
                        "package_code": package_code,
                        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                }
            ]
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to store vector in S3 Vectors",
                "details": str(e)
            })
        }

    # ---------- 6. Success Response ----------
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Vector stored successfully",
            "vector_key": vector_key,
            "embedding_length": len(embedding)
        })
    }