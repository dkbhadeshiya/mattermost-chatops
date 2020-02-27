from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import pymysql
from Chatops import config, dialogflowfile, run
import boto3


@csrf_exempt
def permission(request):
    data = json.loads(request.body)
    if 'channel_id' in data:
        action = json.loads(data['context']['action'])

        """connect mysql database"""
        db = pymysql.connect(config.DB_URL, config.DB_USER, config.DB_PASSWORD, config.DB_NAME, port=config.DB_PORT)
        cursor = db.cursor()

        query_f = f'select status from user_instanceoperation where id="{action["request_id"]}"'
        cursor.execute(query_f)
        db_status = cursor.fetchall()

        if db_status[0][0] == 'Pending':
            status = action['status']

            """get user data"""
            query_f = f'select name,channel_id from user_botuser where id="{action["user"]}"'
            cursor.execute(query_f)
            user = cursor.fetchall()

            msg_status = ''

            if status == 'Accept':
                query_u = f'update user_instanceoperation set status="Accepted", response_by_id="{action["manager_id"]}", ' \
                          f'response_date="{datetime.utcnow()}" where id="{action["request_id"]}" '
                cursor.execute(query_u)
                db.commit()

                message = action['message']

                dialogflow = dialogflowfile.call_dialogflow(message)

                ec2client = boto3.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                         aws_secret_access_key=config.aws_secret_access_key,
                                         region_name=config.region_name)

                if action['type'] == 'scale_instance':
                    instance_name = dialogflow['entities']['any']
                    instance_type = dialogflow['entities']['any1']

                    response = ec2client.describe_instances()
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            if 'Tags' in instance:
                                for tag in instance['Tags']:
                                    if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                                        instance_id = instance['InstanceId']
                                        run.scale_instance(ec2client, data['channel_id'], instance_name, instance_type,
                                                           data['user_id'], instance_id, user[0][0], db)
                else:
                    instance_name = dialogflow['entities']['any']
                    response = ec2client.describe_instances()
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            if 'Tags' in instance:
                                for tag in instance['Tags']:
                                    if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                                        if action['type'] == 'start_instance':
                                            if instance['State']['Name'] != 'running':
                                                instance_id = instance['InstanceId']
                                                run.start_instance(ec2client, data['channel_id'], instance_name,
                                                                   data['user_id'], instance_id, user[0][0], db)

                                        elif action['type'] == 'stop_instance':
                                            if instance['State']['Name'] != 'stopped':
                                                instance_id = instance['InstanceId']
                                                run.stop_instance(ec2client, data['channel_id'], instance_name,
                                                                  data['user_id'], instance_id, user[0][0], db)

                                        else:
                                            if instance['State']['Name'] == 'running':
                                                instance_id = instance['InstanceId']
                                                run.reboot_instance(ec2client, data['channel_id'], instance_name,
                                                                    data['user_id'], instance_id, user[0][0], db)
                msg_status = 'approved'

            if status == 'Reject':
                query_u = f'update user_instanceoperation set status="Rejected", response_by_id="{action["manager_id"]}", response_date="{datetime.utcnow()}" where id="{action["request_id"]}" '
                cursor.execute(query_u)
                db.commit()

                """Get manager name"""
                query_f = f'select name from user_botuser where id="{action["manager_id"]}"'
                cursor.execute(query_f)
                manager = cursor.fetchall()

                message = action['message']

                dialogflow = dialogflowfile.call_dialogflow(message)

                instance_name = dialogflow['entities']['any']

                run.reject_request(user[0][1], manager[0][0], instance_name, action['type'])

                msg_status = 'disapproved'

            return JsonResponse({"update": {"message": f"> @{user[0][0]} has requested to start instance **{instance_name}**\nThe request has been {msg_status}", 'props': {'attachments': []}}})
        else:
            return JsonResponse({"ephemeral_text": f"The selected request is already {db_status[0][0]}"})
    else:
        return HttpResponse('')
