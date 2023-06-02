import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
target_group_arn = os.environ['TARGET_GROUP_ARN']

def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))

    alarm_name = message['AlarmName']
    old_state = message['OldStateValue']
    new_state = message['NewStateValue']
    #reason = message['NewStateReason']
    target_id = message['Trigger']['Dimensions'][0]['value']
    elbv2_client = boto3.client('elbv2')

    # Check Alarm State
    if new_state == 'ALARM' and old_state == 'OK':
        #Check if instance is still in the Target Group. if not, do nothing
        h_response = elbv2_client.describe_target_health(
            TargetGroupArn=target_group_arn,
            Targets=[
                {
                    'Id': target_id
                }
            ]
        )

        # Deregister the target from the target group
        response = elbv2_client.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=[
                {
                    'Id': target_id
                }
            ]
        )

        # Check if the target was successfully deregistered
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Target {} successfully deregistered from target group {}.'.format(target_id,target_group_arn))
        else:
            print('Error: Target {} could not be deregistered from target group {}.'.format(target_id,target_group_arn))

    elif new_state == 'OK' and old_state == 'ALARM':
        # Register the target back to the target group
        r_response = elbv2_client.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=[
                {
                    'Id': target_id
                }
            ]
        )
        # Check if the target was successfully registered
        if r_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Target {} successfully registered from target group {}.'.format(target_id, target_group_arn))
        else:
            print('Error: Target {} could not be registered from target group {}.'.format(target_id, target_group_arn))
    else:
        print('New Alarm State is {}, Old Alarm State is {}. No Action Needed'.format(new_state, old_state))
