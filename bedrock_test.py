"""
最小化测试：验证Bedrock能不能成功调用。
跑完如果报错，报错信息会精确指向卡在哪一步：
  - Model access没申请 → AccessDeniedException，提示去Bedrock console的Model access页面申请
  - Service Quotas不够 → ThrottlingException / LimitExceededException
  - IAM权限不对 → AccessDeniedException，提示缺bedrock:InvokeModel这类权限
  - 区域不支持该模型 → ValidationException，提示模型在这个region不可用

用法：
    python3 bedrock_test.py
"""
import boto3
import json

# 悉尼区域Bedrock模型覆盖有限，大部分模型要用us-east-1或us-west-2
REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

client = boto3.client("bedrock-runtime", region_name=REGION)

try:
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "say hello in one sentence"}],
        }),
    )
    result = json.loads(response["body"].read())
    print("✅ Bedrock调用成功")
    print(result)
except Exception as e:
    print(f"❌ 调用失败: {type(e).__name__}: {e}")
