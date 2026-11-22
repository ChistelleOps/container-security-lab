import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:AutoStop", "Values": ["true"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    ids = [
        inst["InstanceId"]
        for res in resp["Reservations"]
        for inst in res["Instances"]
    ]
    if ids:
        ec2.stop_instances(InstanceIds=ids)
    print(f"Stopped: {ids}")
    return {"stopped": ids}
