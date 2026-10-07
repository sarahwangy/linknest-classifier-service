"""
SQS+Lambda解耦练习——生产者脚本，往SQS队列发一条测试消息。
发送后，SQS会自动触发linknest-sqs-consumer这个Lambda函数去消费这条消息。

用法：
    python3 sqs_lambda_test.py
"""
import boto3
import json

QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/348364741787/linknest-classify-queue"

sqs = boto3.client('sqs', region_name='ap-southeast-2')

response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps({"title": "AWS SAA第7步SQS Lambda解耦练习测试消息"})
)

print(f"✅ 消息已发送，MessageId: {response['MessageId']}")
print("去CloudWatch Logs查linknest-sqs-consumer这个Lambda函数的日志，确认它有没有被自动触发并处理成功")
