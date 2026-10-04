"""
Deploy the fine-tuned DistilBERT classifier (model/) to a SageMaker Serverless
endpoint, using AWS's pre-built Hugging Face Inference DLC.

Usage:
    .venv/bin/python deploy_sagemaker.py
"""

from sagemaker.huggingface import HuggingFaceModel
from sagemaker.serverless import ServerlessInferenceConfig

ROLE = "arn:aws:iam::348364741787:role/linknest-sagemaker-execution-role"
MODEL_DATA = "s3://sarahwang-linknest-distilbert/model.tar.gz"
ENDPOINT_NAME = "linknest-distilbert-serverless"

huggingface_model = HuggingFaceModel(
    model_data=MODEL_DATA,
    role=ROLE,
    transformers_version="4.51",
    pytorch_version="2.6",
    py_version="py312",
    env={"HF_TASK": "text-classification"},  # 10.3实测：不设这个会导致 DistilBERT forward() 报 token_type_ids 参数错误
)

serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=3072,  # 账号配额上限，10.3实测4096会报ResourceLimitExceeded
    max_concurrency=5,
)

if __name__ == "__main__":
    predictor = huggingface_model.deploy(
        serverless_inference_config=serverless_config,
        endpoint_name=ENDPOINT_NAME,
    )
    print(f"\n✅ Deployed. Endpoint name: {predictor.endpoint_name}")
