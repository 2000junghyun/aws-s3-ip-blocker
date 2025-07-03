import json
import boto3
import os
from datetime import datetime

# 환경 변수로 SNS 토픽 ARN 설정
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

sns_client = boto3.client("sns")

def lambda_handler(event, context):
    try:
        # EventBridge 이벤트의 상세 내용 추출
        detail = event.get("detail", {})
        source_ip = detail.get("sourceIPAddress", "N/A")
        event_name = detail.get("eventName", "N/A")
        bucket_name = detail.get("requestParameters", {}).get("bucketName", "N/A")
        object_key = detail.get("requestParameters", {}).get("key", "N/A")
        event_time = event.get("time", datetime.utcnow().isoformat())
        aws_region = event.get("region", "N/A")
        user_agent = detail.get("userAgent", "N/A")
        user_identity = detail.get("userIdentity", {})

        # 사용자 정보
        user_arn = user_identity.get("arn", "N/A")
        user_type = user_identity.get("type", "N/A")
        account_id = user_identity.get("accountId", "N/A")
        mfa_authenticated = user_identity.get("sessionContext", {}).get("attributes", {}).get("mfaAuthenticated", "N/A")

        # 읽기 전용 여부 판단
        read_only = detail.get("readOnly", "N/A")

        # 알림 메시지 구성
        message = f"""
S3 Access Denied Detected

--- Event Details ---
Event Time: {event_time}
AWS Region: {aws_region}
Recipient Account ID: {account_id}

--- Action Details ---
Event Name: {event_name}
Source IP Address: {source_ip}
User Agent: {user_agent}
Read-Only Operation: {read_only}

--- User Identity ---
User Type: {user_type}
User ARN: {user_arn}
MFA Authenticated: {mfa_authenticated}

--- S3 Resource Details ---
Bucket Name: {bucket_name}
Object Key (if applicable): {object_key}

For full event details, check CloudWatch Logs or CloudTrail Event History.
"""

        # SNS 알림 발송
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[ALERT] S3 Access Denied Attempt Detected IP: {source_ip}",
            Message=message.strip()
        )

        print("[+] SNS message sent successfully:", response['MessageId'])

        return {
            "statusCode": 200,
            "body": json.dumps("Notification sent successfully")
        }

    except Exception as e:
        print("[!] Error occurred:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error: {str(e)}")
        }