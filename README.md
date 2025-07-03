# aws-s3-ip-blocker
## Problem

- **Unauthorized external IPs** may access, leak, or delete S3 data.
- The existing structure is **reactive**, detecting and responding only after the attack.
- Difficult to identify abnormal behavior, leading to **false positives or missed detections**.

## Solution Overview

1. An IP address **not on the whitelist** attempts to invoke an S3 API (e.g., `GetObject`).
2. The request is **preemptively blocked** by the S3 Bucket Policy → `AccessDenied` is triggered.
3. The `AccessDenied` event is recorded in **AWS CloudTrail** and sent to **Amazon EventBridge**.
4. EventBridge evaluates the event against a defined **event pattern**.
5. If matched, the rule triggers an **AWS Lambda function**.
6. The Lambda function extracts relevant information from the event data.
7. The function publishes a notification message to an **SNS topic** (`SNS_TOPIC_ARN`).
8. The SNS topic then sends the message to **subscribed email addresses**.
9. The administrator receives **real-time notifications** about the blocked IP and its activity details.

### 1. Bucket Policy Configuration

**Path:**

Amazon S3 → Buckets → Select bucket → Permissions → Bucket policy

```json
json
CopyEdit
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlyFromWhitelistedIPs",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::threatlab-sensitive-data",
        "arn:aws:s3:::threatlab-sensitive-data/*"
      ],
      "Condition": {
        "NotIpAddress": {
          "aws:SourceIp": [
            "70.168.153.114"
          ]
        }
      }
    }
  ]
}

```

**Explanation:**

- `"Effect": "Deny"`: Denies all requests matching the condition.
- `"NotIpAddress"`: Blocks any request not from the specified IP address.
- `"Principal": "*"`: Applies to all users (IAM users, roles, anonymous).
- `"Action": "s3:*"`: Applies to all S3 actions (`PutObject`, `GetObject`, `DeleteObject`, etc.).
- `"Resource"`: Applies to the entire bucket and all its objects.

---

### 2. Create Amazon SNS Topic

**Path:**

Amazon SNS → Topics → Create topic

- **Name:** `S3AccessDenied`
- **Display name:** `AWS Security Alert (S3AccessDenied)`

**Then:**

Select the topic → Go to **Subscriptions** → Create subscription

- **Protocol:** `Email`
- **Endpoint:** `2000junghyun@gmail.com`

---

### 3. Create Lambda Function

**Path:**

AWS Lambda → Functions → Create function

- **Function name:** `S3AccessDenied_AlertHandler`
- **Runtime:** Python 3.9
- **Architecture:** x86_64

### Environment Variables

| **Key** | **Value** |
| --- | --- |
| `SNS_TOPIC_ARN` | ARN of the SNS topic created in Step 2 |

---

### 4. Add SNS Publish Permissions to Lambda

**Path:**

Lambda → Functions → Select function → Configuration → Permissions

Attach a custom policy, e.g., `S3AccessDenied-SNS-Policy`:

```json
json
CopyEdit
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "SNS_TOPIC_ARN"
    }
  ]
}

```

- `SNS_TOPIC_ARN`: The ARN of the SNS topic created in Step 2.

---

### 5. Add EventBridge Trigger

**Path:**

Amazon EventBridge → Rules → Create rule

- **Name:** `S3AccessDeniedMonitor`

**Event Pattern:**

```json
json
CopyEdit
{
  "source": ["aws.s3"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "errorCode": ["AccessDenied"],
    "eventName": [
      "PutObject",
      "GetObject",
      "DeleteObjects",
      "ListObjects",
      "ListObjectsV2"
    ]
  }
}

```

- **Target:** Lambda function → `S3AccessDenied_AlertHandler`

Then, in the Lambda function:

**Path:**

Function overview → Add trigger

- **Trigger type:** EventBridge (CloudWatch Events)
- **Rule:** Existing rules → `S3AccessDeniedMonitor`

## Results

- **Access from unregistered IPs is denied** when attempting to interact with the S3 bucket

<img width="756" alt="image" src="https://github.com/user-attachments/assets/957ff753-2539-4461-a3e0-257067bd3132" />

- **Alert emails are sent** upon detection of such events

![image2](https://github.com/user-attachments/assets/23884f9c-f50f-400e-a71c-c73f53452fd1)

---

## Expected Benefits

- **Prevents data leaks and tampering** by proactively blocking unauthorized IP access to S3
- **Enables real-time detection and notification** of `AccessDenied` attempts
- **Improves auditability and traceability** through CloudTrail logs and SNS-based alerts
