import boto3

s3 = boto3.client('s3')
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'sarahwang-linknest-s3-practice', 'Key': 'logo.png'},
    ExpiresIn=300  # 300秒后过期，5分钟
)
print(url)
