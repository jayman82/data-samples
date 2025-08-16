import random
# --- Per-service usage multipliers for realistic spend simulation ---
# Based on industry AWS spend breakdowns (FinOps Foundation, AWS Cost Explorer, public benchmarks):
# - EC2: largest (30–40% typical), S3: 15–20%, RDS: 10–15%, Lambda: 5–10%,
# - Redshift/Aurora/DynamoDB/FSx/EMR: 5–10% each, ECS/EKS: 5%, CloudFront: 2–5%,
# - ElastiCache/SageMaker/Glue/Athena: 1–3%, Macie/GuardDuty/WAF/etc.: <1%, IAM/CostExplorer: negligible
SERVICE_USAGE_MULTIPLIER = {
    'EC2': 100,           # 30–40% of total spend
    'S3': 60,             # 15–20%
    'RDS': 40,            # 10–15%
    'Lambda': 20,         # 5–10%
    'Redshift': 18,       # 5–10%
    'Aurora': 15,         # 5–10%
    'DynamoDB': 12,       # 5–10%
    'FSx': 10,            # 5–10%
    'EMR': 10,            # 5–10%
    'ECS': 8,             # ~5%
    'EKS': 8,             # ~5%
    'CloudFront': 6,      # 2–5%
    'ElastiCache': 5,     # 1–3%
    'SageMaker': 5,       # 1–3%
    'Glue': 4,            # 1–3%
    'Athena': 4,          # 1–3%
    'Bedrock': 2,         # 1–2%
    'Backup': 2,          # 1–2%
    'StepFunctions': 1.5, # <1%
    'SNS': 1.2,           # <1%
    'SQS': 1.2,           # <1%
    'CloudWatch': 1.2,    # <1%
    'QuickSight': 1,      # <1%
    'DirectConnect': 1,   # <1%
    'TransitGateway': 1,  # <1%
    'AppSync': 0.8,       # <1%
    'WAF': 0.5,           # <1%
    'GuardDuty': 0.3,     # <1%
    'Macie': 0.2,         # <1%
    'VPC': 0.1,           # negligible
    'IAM': 0.05,          # negligible
    'CostExplorer': 0.05, # negligible
}

SERVICE_REGION_MAP = {
    'EC2': ['us-east-1', 'us-west-2', 'eu-west-1'],
    'S3': ['us-east-1', 'us-west-2', 'eu-west-1'],
    'Lambda': ['us-east-1', 'us-west-2'],
    'RDS': ['us-east-1', 'us-west-2'],
    'DynamoDB': ['us-east-1', 'us-west-2'],
    'Redshift': ['us-east-1', 'us-west-2'],
    'CloudFront': ['us-east-1'],
    'EKS': ['us-east-1', 'us-west-2', 'eu-west-1'],
    'ECS': ['us-east-1', 'us-west-2', 'eu-west-1'],
    'Aurora': ['us-east-1', 'us-west-2'],
    'ElastiCache': ['us-east-1', 'us-west-2'],
    'SageMaker': ['us-east-1', 'us-west-2'],
    'Glue': ['us-east-1', 'us-west-2'],
    'Athena': ['us-east-1', 'us-west-2'],
    'Kinesis': ['us-east-1', 'us-west-2'],
    'WAF': ['us-east-1', 'us-west-2'],
    'GuardDuty': ['us-east-1', 'us-west-2'],
    'Macie': ['us-east-1', 'us-west-2'],
    'StepFunctions': ['us-east-1', 'us-west-2'],
    'SNS': ['us-east-1', 'us-west-2'],
    'SQS': ['us-east-1', 'us-west-2'],
    'CloudWatch': ['us-east-1', 'us-west-2'],
    'Bedrock': ['us-east-1', 'us-west-2'],
    'EMR': ['us-east-1', 'us-west-2'],
    'FSx': ['us-east-1', 'us-west-2'],
    'Backup': ['us-east-1', 'us-west-2'],
    'AppSync': ['us-east-1', 'us-west-2'],
    'QuickSight': ['us-east-1', 'us-west-2'],
    'DirectConnect': ['us-east-1', 'us-west-2'],
    'TransitGateway': ['us-east-1', 'us-west-2'],
    'VPC': ['us-east-1', 'us-west-2'],
    'IAM': ['us-east-1'],
    'CostExplorer': ['us-east-1'],
}

RESOURCE_ID_PATTERNS = {
    'EC2': lambda: f"i-{random.getrandbits(48):012x}",
    'S3': lambda: f"bucket-{random.randint(1000,9999)}",
    'Lambda': lambda: f"lambda-func-{random.randint(10000,99999)}",
    'RDS': lambda: f"db-{random.getrandbits(48):012x}",
    'DynamoDB': lambda: f"table-{random.randint(1000,9999)}",
    'Redshift': lambda: f"cluster-{random.randint(1000,9999)}",
    'CloudFront': lambda: f"E{random.getrandbits(32):08x}",
    'EKS': lambda: f"eks-cluster-{random.randint(1000,9999)}",
    'ECS': lambda: f"ecs-cluster-{random.randint(1000,9999)}",
    'Aurora': lambda: f"aurora-db-{random.randint(1000,9999)}",
    'ElastiCache': lambda: f"cache-cluster-{random.randint(1000,9999)}",
    'SageMaker': lambda: f"sagemaker-job-{random.randint(1000,9999)}",
    'Glue': lambda: f"glue-job-{random.randint(1000,9999)}",
    'Athena': lambda: f"athena-query-{random.randint(100000,999999)}",
    'Kinesis': lambda: f"kinesis-stream-{random.randint(1000,9999)}",
    'WAF': lambda: f"waf-{random.randint(1000,9999)}",
    'GuardDuty': lambda: f"gd-detector-{random.randint(1000,9999)}",
    'Macie': lambda: f"macie-session-{random.randint(1000,9999)}",
    'StepFunctions': lambda: f"stepfn-{random.randint(1000,9999)}",
    'SNS': lambda: f"sns-topic-{random.randint(1000,9999)}",
    'SQS': lambda: f"sqs-queue-{random.randint(1000,9999)}",
    'CloudWatch': lambda: f"cw-alarm-{random.randint(1000,9999)}",
    'Bedrock': lambda: f"bedrock-model-{random.randint(1000,9999)}",
    'EMR': lambda: f"j-{random.randint(100000,999999)}",
    'FSx': lambda: f"fsx-{random.randint(1000,9999)}",
    'Backup': lambda: f"backup-vault-{random.randint(1000,9999)}",
    'AppSync': lambda: f"appsync-api-{random.randint(1000,9999)}",
    'QuickSight': lambda: f"qs-dashboard-{random.randint(1000,9999)}",
    'DirectConnect': lambda: f"dxcon-{random.randint(1000,9999)}",
    'TransitGateway': lambda: f"tgw-{random.randint(1000,9999)}",
    'VPC': lambda: f"vpc-{random.randint(1000,9999)}",
    'IAM': lambda: f"iam-role-{random.randint(1000,9999)}",
    'CostExplorer': lambda: f"ce-report-{random.randint(1000,9999)}",
}

USAGE_TYPE_MAP = {
    'EC2': ['BoxUsage', 'CPUCredits'],
    'S3': ['TimedStorage-ByteHrs', 'Requests-Tier1'],
    'Lambda': ['Duration', 'Requests'],
    'RDS': ['InstanceUsage', 'Storage'],
    'DynamoDB': ['ReadCapacityUnit', 'WriteCapacityUnit'],
    'Redshift': ['NodeUsage', 'BackupStorage'],
    'CloudFront': ['Requests', 'DataTransfer-Out-Bytes'],
    'EKS': ['ClusterHours', 'FargatePodSeconds'],
    'ECS': ['ClusterHours', 'TaskHours'],
    'Aurora': ['InstanceUsage', 'IORequests'],
    'ElastiCache': ['NodeUsage', 'BackupStorage'],
    'SageMaker': ['MLComputeTime', 'InferenceRequests'],
    'Glue': ['DPU-Hours', 'CrawledObjects'],
    'Athena': ['Query', 'DataScannedInBytes'],
    'Kinesis': ['PUTPayloadUnits', 'GetRecords'],
    'WAF': ['WebACLUsage', 'RuleEvaluations'],
    'GuardDuty': ['Finding', 'AnalyzedBytes'],
    'Macie': ['ClassificationJobs', 'AnalyzedBytes'],
    'StepFunctions': ['StateTransitions', 'ExecutionTime'],
    'SNS': ['Notification', 'PublishRequests'],
    'SQS': ['Request', 'MessageTransfer'],
    'CloudWatch': ['Metrics', 'LogsIngested'],
    'Bedrock': ['Inference', 'Training'],
    'EMR': ['InstanceHours', 'Storage'],
    'FSx': ['Storage', 'ThroughputCapacity'],
    'Backup': ['BackupStorage', 'RestoreRequests'],
    'AppSync': ['Query', 'Mutation'],
    'QuickSight': ['Session', 'SPICECapacity'],
    'DirectConnect': ['ConnectionHours', 'DataTransfer'],
    'TransitGateway': ['AttachmentHours', 'DataTransfer'],
    'VPC': ['VPCPeering', 'NATGatewayHours'],
    'IAM': ['APIRequest', 'UserCount'],
    'CostExplorer': ['APIRequest', 'ReportGeneration'],
}


def get_rate_for_service(service, usage_type):
    rates = {
        ('EC2', 'BoxUsage'): 0.12,
        ('EC2', 'CPUCredits'): 0.09,
        ('S3', 'TimedStorage-ByteHrs'): 0.023/730,
        ('S3', 'Requests-Tier1'): 0.0004,
        ('Lambda', 'Duration'): 0.00001667,
        ('Lambda', 'Requests'): 0.0000002,
        ('RDS', 'InstanceUsage'): 0.25,
        ('RDS', 'Storage'): 0.10/730,
        ('DynamoDB', 'ReadCapacityUnit'): 0.00013,
        ('DynamoDB', 'WriteCapacityUnit'): 0.00065,
        ('Redshift', 'NodeUsage'): 0.25,
        ('Redshift', 'BackupStorage'): 0.024/730,
        ('CloudFront', 'Requests'): 0.000001,
        ('CloudFront', 'DataTransfer-Out-Bytes'): 0.00008,
        ('EKS', 'ClusterHours'): 0.10,
        ('EKS', 'FargatePodSeconds'): 0.000011244,
        ('ECS', 'ClusterHours'): 0.09,
        ('ECS', 'TaskHours'): 0.05,
        ('Aurora', 'InstanceUsage'): 0.30,
        ('Aurora', 'IORequests'): 0.0002,
        ('ElastiCache', 'NodeUsage'): 0.20,
        ('ElastiCache', 'BackupStorage'): 0.025/730,
        ('SageMaker', 'MLComputeTime'): 0.42,
        ('SageMaker', 'InferenceRequests'): 0.0002,
        ('Glue', 'DPU-Hours'): 0.44,
        ('Glue', 'CrawledObjects'): 0.0001,
        ('Athena', 'Query'): 0.002,
        ('Athena', 'DataScannedInBytes'): 0.000000005,
        ('Kinesis', 'PUTPayloadUnits'): 0.014,
        ('Kinesis', 'GetRecords'): 0.0000004,
        ('WAF', 'WebACLUsage'): 0.60,
        ('WAF', 'RuleEvaluations'): 0.000001,
        ('GuardDuty', 'Finding'): 0.80,
        ('GuardDuty', 'AnalyzedBytes'): 0.000000001,
        ('Macie', 'ClassificationJobs'): 1.25,
        ('Macie', 'AnalyzedBytes'): 0.000000001,
        ('StepFunctions', 'StateTransitions'): 0.000025,
        ('StepFunctions', 'ExecutionTime'): 0.00001667,
        ('SNS', 'Notification'): 0.0000005,
        ('SNS', 'PublishRequests'): 0.0000005,
        ('SQS', 'Request'): 0.0000004,
        ('SQS', 'MessageTransfer'): 0.0000002,
        ('CloudWatch', 'Metrics'): 0.30,
        ('CloudWatch', 'LogsIngested'): 0.0000005,
        ('Bedrock', 'Inference'): 0.002,
        ('Bedrock', 'Training'): 0.01,
        ('EMR', 'InstanceHours'): 0.27,
        ('EMR', 'Storage'): 0.025/730,
        ('FSx', 'Storage'): 0.13/730,
        ('FSx', 'ThroughputCapacity'): 0.05,
        ('Backup', 'BackupStorage'): 0.05/730,
        ('Backup', 'RestoreRequests'): 0.0005,
        ('AppSync', 'Query'): 0.0004,
        ('AppSync', 'Mutation'): 0.0004,
        ('QuickSight', 'Session'): 0.30,
        ('QuickSight', 'SPICECapacity'): 0.25,
        ('DirectConnect', 'ConnectionHours'): 0.08,
        ('DirectConnect', 'DataTransfer'): 0.00002,
        ('TransitGateway', 'AttachmentHours'): 0.06,
        ('TransitGateway', 'DataTransfer'): 0.00002,
        ('VPC', 'VPCPeering'): 0.01,
        ('VPC', 'NATGatewayHours'): 0.045,
        ('IAM', 'APIRequest'): 0.000001,
        ('IAM', 'UserCount'): 0.0,
        ('CostExplorer', 'APIRequest'): 0.00001,
        ('CostExplorer', 'ReportGeneration'): 0.0001,
    }
    return rates.get((service, usage_type), 0.01)
