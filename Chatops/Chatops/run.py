import math
from mattermostdriver import Driver, Websocket
import json
from Chatops import config, dialogflowfile, instances
import asyncio
import threading
import boto3
import boto3.session
import requests
from datetime import datetime
from botocore.exceptions import ClientError
from threading import Lock
import sqlalchemy as db

"""Send codeship notification to the user"""


def send_notification(channel_id, props):
    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': "",
        "props": props})


"""If manager reject the request send message to the requested user"""


def reject_request(channel_id, reject_person, instance_name, type):
    if type == 'scale_instance':
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': f"Your request to scale **{instance_name}** was rejected by @{reject_person}. Please note that no "
                       f"actions has been taken for that instance. "
        })
    elif type == 'start_instance':
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': f"Your request to start **{instance_name}** was rejected by @{reject_person}. Please note that no "
                       f"actions has been taken for that instance. "
        })
    elif type == 'stop_instance':
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': f"Your request to stop **{instance_name}** was rejected by @{reject_person}. Please note that no "
                       f"actions has been taken for that instance. "
        })
    else:
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': f"Your request to reboot **{instance_name}** was rejected by @{reject_person}. Please note that no "
                       f"actions has been taken for that instance. "
        })


"""Check Permission the user is able to scale the instance or not"""


def check_permission(user_id, instance_name, channel_id, message, instance_type, type, engine, connection):
    metadata = db.MetaData()
    table_instances = db.Table('user_instance', metadata, autoload=True, autoload_with=engine)
    query_f = db.select([table_instances.columns.id, table_instances.columns.name]).where(table_instances.columns.name == instance_name)
    resultproxy = connection.execute(query_f)
    instances = resultproxy.fetchall()

    try:
        instance_id = instances[0][0]
    except IndexError:
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': "Instance name is not found."})
        return

    table_manager = db.Table('user_manager', metadata, autoload=True, autoload_with=engine)
    query_f = db.select([table_manager.columns.manager_id_id]).where(table_manager.columns.instance_id_id == instance_id)
    resultproxy = connection.execute(query_f)
    managers = resultproxy.fetchall()

    managers_id = []
    for manager in managers:
        managers_id.append(manager[0])

    table_botuser = db.Table('user_botuser', metadata, autoload=True, autoload_with=engine)
    query_f = db.select([table_botuser.columns.id, table_botuser.columns.name]).where(table_botuser.columns.user_id == user_id)
    resultproxy = connection.execute(query_f)
    users = resultproxy.fetchall()

    user = users[0][0]
    user_name = users[0][1]
    if managers and user not in managers_id:

        table_instanceoperation = db.Table('user_instanceoperation', metadata, autoload=True, autoload_with=engine)
        query_i = table_instanceoperation.insert().values(requested_user_id=user, message=message,
                                                          channel_id=channel_id, status="Pending",
                                                          created_date=datetime.utcnow())
        row = connection.execute(query_i)
        request_id = row.lastrowid

        manager_set = set()
        for item in managers_id:
            manager_set.add(str(item))

        query_f = db.select([table_botuser.columns.id, table_botuser.columns.channel_id], table_botuser.columns.id.in_(manager_set))
        resultproxy = connection.execute(query_f)
        send_request = resultproxy.fetchall()

        if type == 'scale_instance':
            for item in send_request:
                """action button data"""
                accept_button = json.dumps({'status': 'Accept', 'user': user, 'type': 'scale_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})
                reject_button = json.dumps({'status': 'Reject', 'user': user, 'type': 'scale_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})

                d.posts.create_post(options={
                    "channel_id": item[1],
                    "message": f"@{user_name} is request to scale instance **{instance_name}** with instance type **{instance_type}**",
                    "props": {"attachments": [
                        {
                            "text": "Please Accept or Reject the Request",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "actions": [
                                {
                                    "name": "Accept",
                                    "type": "button",
                                    "value": "Accept",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(accept_button)
                                        }
                                    }
                                },
                                {
                                    "name": "Reject",
                                    "type": "button",
                                    "value": "Reject",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(reject_button)
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                    }})
        elif type == 'start_instance':
            for item in send_request:
                """action button data"""
                accept_button = json.dumps({'status': 'Accept', 'user': user, 'type': 'start_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})
                reject_button = json.dumps({'status': 'Reject', 'user': user, 'type': 'start_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})

                d.posts.create_post(options={
                    "channel_id": item[1],
                    "message": f"@{user_name} is request to start instance **{instance_name}**",
                    "props": {"attachments": [
                        {
                            "text": "Please Accept or Reject the Request",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "actions": [
                                {
                                    "name": "Accept",
                                    "type": "button",
                                    "value": "Accept",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(accept_button)
                                        }
                                    }
                                },
                                {
                                    "name": "Reject",
                                    "type": "button",
                                    "value": "Reject",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(reject_button)
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                    }})
        elif type == 'stop_instance':
            for item in send_request:
                """action button data"""
                accept_button = json.dumps({'status': 'Accept', 'user': user, 'type': 'stop_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})
                reject_button = json.dumps({'status': 'Reject', 'user': user, 'type': 'stop_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})

                d.posts.create_post(options={
                    "channel_id": item[1],
                    "message": f"@{user_name} is request to stop instance **{instance_name}**",
                    "props": {"attachments": [
                        {
                            "text": "Please Accept or Reject the Request",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "actions": [
                                {
                                    "name": "Accept",
                                    "type": "button",
                                    "value": "Accept",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(accept_button)
                                        }
                                    }
                                },
                                {
                                    "name": "Reject",
                                    "type": "button",
                                    "value": "Reject",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(reject_button)
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                    }})
        else:
            for item in send_request:
                """action button data"""
                accept_button = json.dumps({'status': 'Accept', 'user': user, 'type': 'reboot_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})
                reject_button = json.dumps({'status': 'Reject', 'user': user, 'type': 'reboot_instance',
                                            'request_id': request_id, 'manager_id': item[0], 'message': message})

                d.posts.create_post(options={
                    "channel_id": item[1],
                    "message": f"@{user_name} is request to reboot instance **{instance_name}**",
                    "props": {"attachments": [
                        {
                            "text": "Please Accept or Reject the Request",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "actions": [
                                {
                                    "name": "Accept",
                                    "type": "button",
                                    "value": "Accept",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(accept_button)
                                        }
                                    }
                                },
                                {
                                    "name": "Reject",
                                    "type": "button",
                                    "value": "Reject",
                                    "integration": {
                                        "url": f"{config.BASE_URL}/permission",
                                        "context": {
                                            "action": str(reject_button)
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                    }})

        return False
    else:
        table_instanceoperation = db.Table('user_instanceoperation', metadata, autoload=True, autoload_with=engine)
        query_i = table_instanceoperation.insert().values(requested_user_id=user, message=message,
                                                          channel_id=channel_id, status="Accepted",
                                                          created_date=datetime.utcnow(), response_by_id=user,
                                                          response_date=datetime.utcnow())
        connection.execute(query_i)

        return True


"""Check project config in database or not"""


def check_project(project_name, engine, connection):

    """Get all project from database"""
    metadata = db.MetaData()
    table_project = db.Table('user_project', metadata, autoload=True, autoload_with=engine)
    query_f = db.select([table_project.columns.codeship_project_name, table_project.columns.gitlab_project_id])
    resultproxy = connection.execute(query_f)
    projects = resultproxy.fetchall()

    for project in projects:
        if project[0] == project_name:
            return project[1]
    return None


"""Notify the instance access user"""


def notify_stack_holders(instance_name, user_id, requested_user, status, type, engine, connection):

    metadata = db.MetaData()
    table_botuser = db.Table('user_botuser', metadata, autoload=True, autoload_with=engine)
    table_instanceaccess = db.Table('user_instanceaccess', metadata, autoload=True, autoload_with=engine)
    table_instance = db.Table('user_instance', metadata, autoload=True, autoload_with=engine)

    join_query = table_instanceaccess.join(table_botuser, table_instanceaccess.columns.user_id_id == table_botuser.columns.id).join(table_instance, table_instanceaccess.columns.instance_id_id == table_instance.columns.id)
    query = db.select([table_botuser.columns.channel_id, table_botuser.columns.name, table_botuser.columns.user_id]).select_from(join_query).where(table_instance.columns.name == instance_name)
    resultproxy = connection.execute(query)
    users = resultproxy.fetchall()

    query_f = db.select([table_botuser.columns.name]).where(table_botuser.columns.user_id == user_id)
    resultproxy = connection.execute(query_f)
    approve_user = resultproxy.fetchall()

    approve_user = approve_user[0][0]

    if status == 'start':

        for user in users:
            if user[2] != user_id:
                if type == 'scale_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** is getting scaled on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to scale instance **{instance_name}** has been approved by @{approve_user}. Instance is being scaled at the moment, I will update you once it completes. "})
                if type == 'start_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** is getting started on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to start instance **{instance_name}** has been approved by @{approve_user}. Instance is being started at the moment, I will update you once it completes. "})
                if type == 'stop_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** is getting stopped on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to stop instance **{instance_name}** has been approved by @{approve_user}. Instance is being stopped at the moment, I will update you once it completes. "})

    if status == 'end':

        for user in users:
            if user[2] != user_id:
                if type == 'scale_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** has been scaled on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to scale instance **{instance_name}** has been successful. The instance should reflect your requested configuration.  "})
                if type == 'start_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** has been started on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to start instance **{instance_name}** has been successful. The instance should reflect your requested configuration.  "})
                if type == 'stop_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** has been stopped on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to stop instance **{instance_name}** has been successful. The instance should reflect your requested configuration.  "})
                if type == 'reboot_instance':
                    if user[1] != requested_user:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Instance **{instance_name}** has been reboot on request of @{requested_user} "
                                       f"approved by @{approve_user}"})
                    else:
                        d.posts.create_post(options={
                            'channel_id': user[0],
                            'message': f"Your request to reboot instance **{instance_name}** has been successful. The instance should reflect your requested configuration.  "})


"""Get all instance from aws"""


def get_instance(engine, connection):

    session = boto3.session.Session()

    ec2 = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                         aws_secret_access_key=config.aws_secret_access_key,
                         region_name=config.region_name)

    metadata = db.MetaData()
    instances = db.Table('user_instance', metadata, autoload=True, autoload_with=engine)
    q = db.select([instances])
    resultproxy = connection.execute(q)
    db_instances = resultproxy.fetchall()

    all_instance_db = []
    for instance in db_instances:
        all_instance_db.append(instance[2])

    response = ec2.describe_instances()

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = None
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
            if instance['InstanceId'] not in all_instance_db and name:
                q = instances.insert().values(instance_id=instance['InstanceId'], name=name)
                connection.execute(q)


"""scaling, starting, stopping and rebooting the instance"""


def scale_instance(ec2client, channel_id, instance_name, instance_type, user_id, instance_id, requested_user, engine, connection):
    try:
        ec2client.start_instances(InstanceIds=[instance_id], DryRun=True)
        ec2client.stop_instances(InstanceIds=[instance_id], DryRun=True)
        ec2client.modify_instance_attribute(InstanceId=instance_id, Attribute='instanceType',
                                            Value=instance_type, DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "Looks like I do not have permission to scale the instance. Please check that the aws key "
                           "has correct permissions."})
            return

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Please wait, your instance **{instance_name}** is being scaled !"})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'start', 'scale_instance', engine, connection)

    """Changing Instance Type"""

    ec2client.stop_instances(InstanceIds=[instance_id])

    waiter = ec2client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])

    # Change the instance type
    ec2client.modify_instance_attribute(InstanceId=instance_id, Attribute='instanceType',
                                        Value=instance_type)

    # Start the instance
    ec2client.start_instances(InstanceIds=[instance_id])

    waiter = ec2client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'end', 'scale_instance', engine, connection)

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Your instance **{instance_name}** has been scaled successfully to **{instance_type}**"})


def start_instance(ec2client, channel_id, instance_name, user_id, instance_id, requested_user, engine, connection):
    try:
        ec2client.start_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "Looks like I do not have permission to start the instance. Please check that the aws key "
                           "has correct permissions."})
            return

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Please wait, your instance **{instance_name}** is being started :white_check_mark:"})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'start', 'start_instance', engine, connection)

    ec2client.start_instances(InstanceIds=[instance_id], DryRun=False)

    waiter = ec2client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Instance **{instance_name}** is now started :white_check_mark: "})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'end', 'start_instance', engine, connection)


def stop_instance(ec2client, channel_id, instance_name, user_id, instance_id, requested_user, engine, connection):
    try:
        ec2client.stop_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "Looks like I do not have permission to stop the instance. Please check that the aws key "
                           "has correct permissions."})
            return

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Please wait, your instance **{instance_name}** is being stopped :stop_sign:"})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'start', 'stop_instance', engine, connection)

    ec2client.stop_instances(InstanceIds=[instance_id], DryRun=False)

    waiter = ec2client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Instance **{instance_name}** is now stopped :stop_sign:"})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'end', 'stop_instance', engine, connection)


def reboot_instance(ec2client, channel_id, instance_name, user_id, instance_id, requested_user, engine, connection):
    try:
        ec2client.reboot_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "Looks like I do not have permission to reboot the instance. Please check that the aws key "
                           "has correct permissions."})
            return

    ec2client.reboot_instances(InstanceIds=[instance_id], DryRun=False)

    d.posts.create_post(options={
        'channel_id': channel_id,
        'message': f"Instance **{instance_name}** is set to reboot :arrows_counterclockwise: ,  it should reboot in "
                   f"few minutes"})

    """Notify stake holders"""
    notify_stack_holders(instance_name, user_id, requested_user, 'end', 'reboot_instance', engine, connection)


"""New user created in database"""


def create_user(user_id, channel_id, engine, connection):

    metadata = db.MetaData()
    botuser = db.Table('user_botuser', metadata, autoload=True, autoload_with=engine)
    query_f = db.select([botuser]).where(botuser.columns.user_id == user_id)
    resultproxy = connection.execute(query_f)
    this_user = resultproxy.fetchall()

    if not this_user:
        user = d.users.get_user(user_id=user_id)
        q = botuser.insert().values(user_id=user_id, name=user['username'], email=user['email'], channel_id=channel_id,
                                    created_date=datetime.utcnow())
        connection.execute(q)


"""handle all messages intent and according to that send responses to the users"""


def send_message(data):
    """Connect Mysql database"""

    connection_string = f'mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_URL}/{config.DB_NAME}'
    engine = db.create_engine(connection_string)
    connection = engine.connect()
    metadata = db.MetaData()

    post = json.loads(data['data']['post'])
    channel_id = post['channel_id']
    msg = post['message']

    """get entities and intent"""

    dialogflow = dialogflowfile.call_dialogflow(msg)
    intent = ['scale_intent', 'start_instance intent', 'stop_instance intent', 'reboot_instance intent']

    global i_c_p

    if dialogflow['intent'] in intent:
        instance_name = dialogflow['entities']['any']
        if instance_name in i_c_p:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': f'Instance **{instance_name}** is already being processed, please try again after some '
                           f'times to submit a new operation.'
            })
            return
        else:
            lock.acquire()
            i_c_p.update({instance_name: dialogflow['intent']})
            lock.release()

    user_id = post['user_id']
    message = dialogflow['message']

    create_user(user_id, channel_id, engine, connection)

    if dialogflow['intent'] == 'Default Welcome Intent':
        props = {"attachments": [{
            "title": "Welcome to ChatOps, here's some things that I can do for you:",
            "color": "#FFB046",
            "fields": [
                {
                    "short": True,
                    "title": ":cloud: AWS (Cloud)",
                    "value": "1. Status of Instance\n  * status of {_instance_name_}\n1. Scale Instance\n  * scale {"
                             "_instance_name_} to {_instance_type_}\n1. Start Instance\n  * start {"
                             "_instance_name_}\n1. Stop Instance\n  * stop {_instance_name_}\n1. Reboot Instance\n  * "
                             "reboot {_instance_name_}\n1. Search Instance\n  * search {_some_characters_}\n1. List "
                             "of Instances\n  * list instances "
                },
                {
                    "short": True,
                    "title": ":keyboard: Codeship (CI/CD)",
                    "value": "1. Check Commit Deployment\n  * commit {_commit_sha_} on {_project_name_}\n1. Last "
                             "Build Details\n  * last build on {_project_name_}\n1. Last Successful Build Details\n  * "
                             "last successful build on {_project_name_}\n1. Last Failed Build Details\n  * last "
                             "failed build on {_project_name_}"
                }
            ],
        }]}
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': "",
            'props': props})

    elif dialogflow['intent'] == 'status_intent':

        get_instance(engine, connection)

        instance_name = dialogflow['entities']['any']

        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': f"Fetching the status of **{instance_name}** :man_technologist:"})

        cw = boto3.client('cloudwatch', aws_access_key_id=config.aws_access_key_id,
                          aws_secret_access_key=config.aws_secret_access_key,
                          region_name=config.region_name)
        ec2client = boto3.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                 aws_secret_access_key=config.aws_secret_access_key,
                                 region_name=config.region_name)
        found = False
        response = ec2client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                            instance_id = instance['InstanceId']
                            found = True
                            json_cpucredit = json.dumps({"width": 800, "height": 450, "metrics": [["AWS/EC2",
                                                                                                   "CPUCreditBalance",
                                                                                                   "InstanceId",
                                                                                                   instance_id
                                                                                                   ],
                                                                                                  [
                                                                                                      "AWS/EC2",
                                                                                                      "CPUCreditUsage",
                                                                                                      "InstanceId",
                                                                                                      instance_id
                                                                                                  ]
                                                                                                  ],
                                                         "period": 300, "stacked": True, "title": "CPU Credit",
                                                         "view": "timeSeries"})

                            json_cpu = json.dumps({"width": 800, "height": 450, "metrics": [["AWS/EC2",
                                                                                             "CPUUtilization",
                                                                                             "InstanceId",
                                                                                             instance_id
                                                                                             ]
                                                                                            ],
                                                   "period": 300, "stacked": True, "title": "CPU Usage",
                                                   "view": "timeSeries"})

                            json_network = json.dumps({"width": 800, "height": 450, "metrics": [["AWS/EC2",
                                                                                                 "NetworkIn",
                                                                                                 "InstanceId",
                                                                                                 instance_id
                                                                                                 ],
                                                                                                [
                                                                                                    "AWS/EC2",
                                                                                                    "NetworkOut",
                                                                                                    "InstanceId",
                                                                                                    instance_id
                                                                                                ]
                                                                                                ],
                                                       "period": 300, "stacked": True, "title": "Network I/O",
                                                       "view": "timeSeries"})

                            response_cpucredit = cw.get_metric_widget_image(MetricWidget=json_cpucredit)
                            response_cpu = cw.get_metric_widget_image(MetricWidget=json_cpu)
                            response_network = cw.get_metric_widget_image(MetricWidget=json_network)

                            with open('cpucredit.png', 'wb') as f:
                                f.write(response_cpucredit["MetricWidgetImage"])

                            with open('cpu.png', 'wb') as f:
                                f.write(response_cpu["MetricWidgetImage"])

                            with open('network.png', 'wb') as f:
                                f.write(response_network["MetricWidgetImage"])

                            cpu_credit_file_id = d.files.upload_file(
                                channel_id=channel_id,
                                files={'files': (f'{instance_name} Cpu Credit.png', open('cpucredit.png', 'rb'))}
                            )['file_infos'][0]['id']

                            cpu_file_id = d.files.upload_file(
                                channel_id=channel_id,
                                files={'files': (f'{instance_name} Cpu Usage.png', open('cpu.png', 'rb'))}
                            )['file_infos'][0]['id']

                            network_file_id = d.files.upload_file(
                                channel_id=channel_id,
                                files={'files': (f'{instance_name} Network IO.png', open('network.png', 'rb'))}
                            )['file_infos'][0]['id']

                            d.posts.create_post(options={
                                'channel_id': channel_id,
                                'message': f'### {instance_name} instance status:',
                                'file_ids': [cpu_credit_file_id, cpu_file_id, network_file_id],
                            })

                            return
        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find the instance name :bowing_man: , can you please give me correct instance name?"})

    elif dialogflow['intent'] == 'scale_intent':

        get_instance(engine, connection)
        instance_name = dialogflow['entities']['any']
        instance_type = dialogflow['entities']['any1']

        ec2client = boto3.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                 aws_secret_access_key=config.aws_secret_access_key,
                                 region_name=config.region_name)
        found = False

        """Get all instance type from instances.py file"""
        instance_types = instances.instance

        response = ec2client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                            found = True
                            if instance['InstanceType'] == instance_type:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': f"Hang on, {instance_name} is already {instance_type} :bowing_man: "})
                            elif instance_type not in instance_types:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "It is not valid instance type."})
                            else:
                                permission = check_permission(user_id, instance_name, channel_id, message,
                                                              instance_type, 'scale_instance', engine, connection)
                                if permission:
                                    instance_id = instance['InstanceId']
                                    table_botuser = db.Table('user_botuser', metadata, autoload=True,
                                                             autoload_with=engine)
                                    query_f = db.select([table_botuser.columns.name]).where(
                                        table_botuser.columns.user_id == user_id)
                                    resultproxy = connection.execute(query_f)
                                    user = resultproxy.fetchall()

                                    requested_user = user[0][0]
                                    scale_instance(ec2client, channel_id, instance_name, instance_type, user_id,
                                                   instance_id, requested_user, engine, connection)
                                else:
                                    d.posts.create_post(options={
                                        'channel_id': channel_id,
                                        'message': "Your request has been sent to manager for approval. I will keep "
                                                   "you posted on it."
                                    })
                            lock.acquire()
                            del i_c_p[instance_name]
                            lock.release()
                            return
        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find the instance name :bowing_man:, can you please give me correct instance name?"})
        del i_c_p[instance_name]

    elif dialogflow['intent'] == 'commit intent':

        project_name = dialogflow['entities']['any']

        """Check project available or not"""
        project_id = check_project(project_name, engine, connection)

        if project_id:

            commit_id = dialogflow['entities']['commit']

            headers = {
                'PRIVATE-TOKEN': config.GITLAB_ACCESS_TOKEN
            }

            response = requests.get(f'https://gitlab.com/api/v4/projects/{project_id}/repository/commits',
                                    headers=headers)

            if response.status_code != 200:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"I could not fetch Git commits, can you check whether the git configs are correct?"})
            else:
                response = response.json()
                found = False
                for item in response:
                    if commit_id == item['id']:
                        found = True

                        """Get All Commits"""
                        all_commit_id = []
                        for commit in response:
                            all_commit_id.append(commit['id'])

                        this_commit_index = all_commit_id.index(commit_id)

                        commits_deployed = []

                        for commit in range(0, this_commit_index + 1):
                            commits_deployed.append(all_commit_id[commit])

                        """Get Codeship Organazation UUID"""

                        try:
                            get_organization_uuid = requests.post("https://api.codeship.com/v2/auth",
                                                                  auth=(config.CODESHIP_EMAIL,
                                                                        config.CODESHIP_PASSWORD)).json()

                            token = get_organization_uuid['access_token']

                            organization_uuid = get_organization_uuid['organizations'][0]['uuid']
                        except:
                            d.posts.create_post(options={
                                'channel_id': channel_id,
                                'message': "I could not connect to CodeShip, can you check whether the codeship "
                                           "configs are correct?"})
                        else:
                            deploy_found = False
                            project_found = False

                            get_project_uuid = requests.get(
                                f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects",
                                headers={'Authorization': token}).json()

                            for project in get_project_uuid['projects']:
                                name = project['name'].split('/')[-1]
                                if name == project_name:
                                    project_found = True
                                    page = 1
                                    total_page = 1
                                    while page <= total_page:
                                        get_project_build = requests.get(
                                            f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects/{project['uuid']}/builds?per_page=50&page={page}",
                                            headers={'Authorization': token}).json()

                                        total_page = math.ceil(get_project_build['total'] / 50)

                                        page += 1

                                        for build in get_project_build['builds']:
                                            if build['commit_sha'] in commits_deployed:
                                                deploy_found = True
                                                d.posts.create_post(options={
                                                    'channel_id': channel_id,
                                                    'message': f'**Yes**, this Commit **_{commit_id}_** is deployed.'})
                                                return

                            if not project_found:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "I cannot find that project, please check whether the project exists "
                                               "in codeship."})

                            if not deploy_found and project_found:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': f"**No**, this commit **_{commit_id}_** is not deploy."})
                        return

                if not found:
                    d.posts.create_post(options={
                        'channel_id': channel_id,
                        'message': "I am not able to find the commit id **_{commit_id}_**. Are you sure it's correct?"})
        else:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find that project, please check whether the project exists in codeship and "
                           "configured properly in admin panel. "})

    elif dialogflow['intent'] == 'last build intent':

        project_name = dialogflow['entities']['any']

        try:
            get_organization_uuid = requests.post("https://api.codeship.com/v2/auth",
                                                  auth=(config.CODESHIP_EMAIL,
                                                        config.CODESHIP_PASSWORD)).json()

            token = get_organization_uuid['access_token']

            organization_uuid = get_organization_uuid['organizations'][0]['uuid']
        except:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I could not connect to CodeShip, can you check whether the codeship configs are correct?"})
        else:
            deploy_found = False
            project_found = False

            get_project_uuid = requests.get(
                f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects",
                headers={'Authorization': token}).json()

            for project in get_project_uuid['projects']:
                name = project['name'].split('/')[-1]
                if name == project_name:
                    project_found = True

                    get_project_build = requests.get(
                        f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects/{project['uuid']}/builds?per_page=1",
                        headers={'Authorization': token}).json()

                    for build in get_project_build['builds']:
                        status = build['status']

                        if status == 'error':
                            symbol = ':x:'
                            title_text = '(Build failed)'
                            color = '#FF0000'

                        elif status == 'initiated':
                            symbol = ':clock8:'
                            title_text = '(Build initiated)'
                            color = '#00B6FF'

                        elif status == 'stopped':
                            symbol = ':stop_sign:'
                            title_text = '(Build stopped)'
                            color = '#AAAAAA'

                        elif status == 'success':
                            symbol = ':white_check_mark:'
                            title_text = '(Build successful)'
                            color = '#00D637'

                        else:
                            symbol = ''
                            title_text = f'(Build {status})'
                            color = '#C6C6C6'

                        props = {"attachments": [{
                            "title": f"{symbol} {project_name} {title_text}",
                            "color": color,
                            "fields": [
                                {
                                    "short": True,
                                    "title": "Commit Id",
                                    "value": build['commit_sha']
                                },
                                {
                                    "short": True,
                                    "title": "Status",
                                    "value": status
                                },
                                {
                                    "short": True,
                                    "title": "Committer",
                                    "value": build['username']
                                },
                                {
                                    "short": True,
                                    "title": "Branch",
                                    "value": build['branch']
                                }
                            ],
                        }]}
                        deploy_found = True
                        d.posts.create_post(options={
                            'channel_id': channel_id,
                            'message': "",
                            'props': props})
                        return

            if not project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"I cannot find that project, please check whether the project exists in codeship."})

            if not deploy_found and project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"**No** deploy found."})

    elif dialogflow['intent'] == 'last successful build intent':

        project_name = dialogflow['entities']['any']

        try:
            get_organization_uuid = requests.post("https://api.codeship.com/v2/auth",
                                                  auth=(config.CODESHIP_EMAIL,
                                                        config.CODESHIP_PASSWORD)).json()

            token = get_organization_uuid['access_token']

            organization_uuid = get_organization_uuid['organizations'][0]['uuid']
        except:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I could not connect to CodeShip, can you check whether the codeship configs are correct?"})
        else:
            deploy_found = False
            project_found = False

            get_project_uuid = requests.get(
                f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects",
                headers={'Authorization': token}).json()

            for project in get_project_uuid['projects']:
                name = project['name'].split('/')[-1]
                if name == project_name:
                    project_found = True
                    page = 1
                    total_page = 1
                    while page <= total_page:
                        get_project_build = requests.get(
                            f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects/{project['uuid']}/builds?per_page=50&page={page}",
                            headers={'Authorization': token}).json()

                        total_page = math.ceil(get_project_build['total'] / 50)

                        page += 1

                        for build in get_project_build['builds']:
                            if build['status'] == 'success':
                                deploy_found = True
                                props = {"attachments": [{
                                    "title": f":white_check_mark: {project_name} (Build successful)",
                                    "color": "#00D637",
                                    "fields": [
                                        {
                                            "short": True,
                                            "title": "Commit Id",
                                            "value": build['commit_sha']
                                        },
                                        {
                                            "short": True,
                                            "title": "Status",
                                            "value": build['status']
                                        },
                                        {
                                            "short": True,
                                            "title": "Committer",
                                            "value": build['username']
                                        },
                                        {
                                            "short": True,
                                            "title": "Branch",
                                            "value": build['branch']
                                        }
                                    ],
                                }]}
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "",
                                    'props': props})
                                return

            if not project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"I cannot find that project, please check whether the project exists in codeship."})

            if not deploy_found and project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"**No** deploy found."})

    elif dialogflow['intent'] == 'last failed build intent':

        project_name = dialogflow['entities']['any']

        try:
            get_organization_uuid = requests.post("https://api.codeship.com/v2/auth",
                                                  auth=(config.CODESHIP_EMAIL,
                                                        config.CODESHIP_PASSWORD)).json()

            token = get_organization_uuid['access_token']

            organization_uuid = get_organization_uuid['organizations'][0]['uuid']
        except:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I could not connect to CodeShip, can you check whether the codeship configs are correct?"})
        else:
            deploy_found = False
            project_found = False

            get_project_uuid = requests.get(
                f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects",
                headers={'Authorization': token}).json()

            for project in get_project_uuid['projects']:
                name = project['name'].split('/')[-1]
                if name == project_name:
                    project_found = True
                    page = 1
                    total_page = 1
                    while page <= total_page:
                        get_project_build = requests.get(
                            f"https://api.codeship.com/v2/organizations/{organization_uuid}/projects/{project['uuid']}/builds?per_page=50&page={page}",
                            headers={'Authorization': token}).json()

                        total_page = math.ceil(get_project_build['total'] / 50)

                        page += 1

                        for build in get_project_build['builds']:
                            if build['status'] == 'error':
                                deploy_found = True
                                props = {"attachments": [{
                                    "title": f":x: {project_name} (Build failed)",
                                    "color": "#FF0000",
                                    "fields": [
                                        {
                                            "short": True,
                                            "title": "Commit Id",
                                            "value": build['commit_sha']
                                        },
                                        {
                                            "short": True,
                                            "title": "Status",
                                            "value": build['status']
                                        },
                                        {
                                            "short": True,
                                            "title": "Committer",
                                            "value": build['username']
                                        },
                                        {
                                            "short": True,
                                            "title": "Branch",
                                            "value": build['branch']
                                        }
                                    ],
                                }]}
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "",
                                    'props': props})
                                return

            if not project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"I cannot find that project, please check whether the project exists in codeship."})

            if not deploy_found and project_found:
                d.posts.create_post(options={
                    'channel_id': channel_id,
                    'message': f"**No** deploy found."})

    elif dialogflow['intent'] == 'start_instance intent':

        get_instance(engine, connection)

        instance_name = dialogflow['entities']['any']

        session = boto3.session.Session()

        ec2client = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                   aws_secret_access_key=config.aws_secret_access_key,
                                   region_name=config.region_name)
        found = False

        response = ec2client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                            found = True
                            if instance['State']['Name'] != 'running':
                                permission = check_permission(user_id, instance_name, channel_id, message,
                                                              None, 'start_instance', engine, connection)
                                if permission:
                                    instance_id = instance['InstanceId']
                                    table_botuser = db.Table('user_botuser', metadata, autoload=True,
                                                             autoload_with=engine)
                                    query_f = db.select([table_botuser.columns.name]).where(
                                        table_botuser.columns.user_id == user_id)
                                    resultproxy = connection.execute(query_f)
                                    user = resultproxy.fetchall()

                                    requested_user = user[0][0]
                                    start_instance(ec2client, channel_id, instance_name, user_id,
                                                   instance_id, requested_user, engine, connection)
                                else:
                                    d.posts.create_post(options={
                                        'channel_id': channel_id,
                                        'message': "Your request has been sent to manager for approval. I will keep "
                                                   "you posted on it. "
                                    })
                            else:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "The instance that you have requested is already having **running** "
                                               "state"})
                            lock.acquire()
                            del i_c_p[instance_name]
                            lock.release()
                            return
        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find the instance name :bowing_man:, can you please give me correct instance name?"})
        del i_c_p[instance_name]

    elif dialogflow['intent'] == 'stop_instance intent':

        get_instance(engine, connection)

        instance_name = dialogflow['entities']['any']

        session = boto3.session.Session()

        ec2client = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                   aws_secret_access_key=config.aws_secret_access_key,
                                   region_name=config.region_name)
        found = False

        response = ec2client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                            found = True
                            if instance['State']['Name'] != 'stopped':
                                permission = check_permission(user_id, instance_name, channel_id, message,
                                                              None, 'stop_instance', engine, connection)
                                if permission:
                                    instance_id = instance['InstanceId']
                                    table_botuser = db.Table('user_botuser', metadata, autoload=True, autoload_with=engine)
                                    query_f = db.select([table_botuser.columns.name]).where(table_botuser.columns.user_id == user_id)
                                    resultproxy = connection.execute(query_f)
                                    user = resultproxy.fetchall()

                                    requested_user = user[0][0]
                                    stop_instance(ec2client, channel_id, instance_name, user_id,
                                                  instance_id, requested_user, engine, connection)
                                else:
                                    d.posts.create_post(options={
                                        'channel_id': channel_id,
                                        'message': "Your request has been sent to manager for approval. I will keep "
                                                   "you posted on it. "
                                    })
                            else:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': "The instance that you have requested is already having **stopped** "
                                               "state"})
                            lock.acquire()
                            del i_c_p[instance_name]
                            lock.release()
                            return
        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find the instance name :bowing_man:, can you please give me correct instance name?"})
        del i_c_p[instance_name]

    elif dialogflow['intent'] == 'reboot_instance intent':
        get_instance(engine, connection)

        instance_name = dialogflow['entities']['any']

        session = boto3.session.Session()

        ec2client = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                                   aws_secret_access_key=config.aws_secret_access_key,
                                   region_name=config.region_name)
        found = False

        response = ec2client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == instance_name:
                            found = True
                            if instance['State']['Name'] == 'running':
                                permission = check_permission(user_id, instance_name, channel_id, message,
                                                              None, 'reboot_instance', engine, connection)
                                if permission:
                                    instance_id = instance['InstanceId']
                                    table_botuser = db.Table('user_botuser', metadata, autoload=True,
                                                             autoload_with=engine)
                                    query_f = db.select([table_botuser.columns.name]).where(
                                        table_botuser.columns.user_id == user_id)
                                    resultproxy = connection.execute(query_f)
                                    user = resultproxy.fetchall()

                                    requested_user = user[0][0]
                                    reboot_instance(ec2client, channel_id, instance_name, user_id,
                                                    instance_id, requested_user, engine, connection)
                                else:
                                    d.posts.create_post(options={
                                        'channel_id': channel_id,
                                        'message': "Your request has been sent to manager for approval. I will keep "
                                                   "you posted on it. "
                                    })
                            else:
                                d.posts.create_post(options={
                                    'channel_id': channel_id,
                                    'message': f"Instance **{instance_name}** is not **running** state"})
                            lock.acquire()
                            del i_c_p[instance_name]
                            lock.release()
                            return

        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "I cannot find the instance name :bowing_man:, can you please give me correct instance name?"})

        del i_c_p[instance_name]

    elif dialogflow['intent'] == 'list instance intent':

        session = boto3.session.Session()

        ec2 = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                             aws_secret_access_key=config.aws_secret_access_key,
                             region_name=config.region_name)

        response = ec2.describe_instances()
        found = False
        counter = 0
        instance_list = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if counter < 10 and 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            found = True
                            counter += 1
                            instance_list.append(
                                f'| {tag["Value"]} | {instance["State"]["Name"]} | {instance["InstanceType"]} |')

        if found:
            msg = """| Name | Status | Type |
                     |:------------:|:-------------:|:--------------:|"""
            instance_list.insert(0, msg)
            instance_string = '\n'.join(instance_list)
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': instance_string
            })

        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "No any instance found."
            })

    elif dialogflow['intent'] == 'search instance intent':

        instance_name_like = dialogflow['entities']['any']
        max_length = None

        if instance_name_like.strip() == '':
            max_length = 10

        session = boto3.session.Session()

        ec2 = session.client('ec2', aws_access_key_id=config.aws_access_key_id,
                             aws_secret_access_key=config.aws_secret_access_key,
                             region_name=config.region_name)

        response = ec2.describe_instances()
        found = False
        instance_list = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            if instance_name_like in tag['Value']:
                                found = True
                                instance_list.append(
                                    f'| {tag["Value"]} | {instance["State"]["Name"]} | {instance["InstanceType"]} |')

        if max_length and len(instance_list) > 10:
            instance_list = instance_list[:10]

        if found:
            msg = """| Name | Status | Type |
                             |:------------:|:-------------:|:--------------:|"""
            instance_list.insert(0, msg)
            instance_string = '\n'.join(instance_list)
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': instance_string
            })

        if not found:
            d.posts.create_post(options={
                'channel_id': channel_id,
                'message': "No any instance found."
            })

    else:
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': "Sorry I could not understand what you're trying to say."})
        props = {"attachments": [{
            "title": "Here are few things I can do:",
            "color": "#FFB046",
            "fields": [
                {
                    "short": True,
                    "title": ":cloud: AWS (Cloud)",
                    "value": "1. Status of Instance\n  * status of {_instance_name_}\n1. Scale Instance\n  * scale {"
                             "_instance_name_} to {_instance_type_}\n1. Start Instance\n  * start {"
                             "_instance_name_}\n1. Stop Instance\n  * stop {_instance_name_}\n1. Reboot Instance\n  * "
                             "reboot {_instance_name_}\n1. Search Instance\n  * search {_some_characters_}\n1. List "
                             "of Instances\n  * list instances "
                },
                {
                    "short": True,
                    "title": ":keyboard: Codeship (CI/CD)",
                    "value": "1. Check Commit Deployment\n  * commit {_commit_sha_} on {_project_name_}\n1. Last "
                             "Build Details\n  * last build on {_project_name_}\n1. Last Successful Build Details\n  * "
                             "last successful build on {_project_name_}\n1. Last Failed Build Details\n  * last "
                             "failed build on {_project_name_}"
                }
            ],
        }]}
        d.posts.create_post(options={
            'channel_id': channel_id,
            'message': "",
            'props': props})


async def event_handler(messages):
    data = json.loads(messages)
    if 'event' in data:
        if 'post' in data['data'] and 'sender_name' in data['data']:
            sender = data['data']['sender_name']
            if data['event'] == 'posted' and sender != '@' + config.BOT_NAME:
                threading.Thread(target=send_message, args=(data,)).start()


"""override the Mattermost 'Driver' class"""


class driver(Driver):

    def init_websocket(self, event_handler, websocket_cls=Websocket):
        self.websocket = websocket_cls(self.options, self.client.token)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.websocket.connect(event_handler))
        return loop


def start():
    d.init_websocket(event_handler)


"""Connect Mattermost driver"""
d = driver({'url': config.URL, 'token': config.BOT_TOKEN, 'scheme': config.SCHEME})
d.login()

lock = Lock()
i_c_p = {}  # Instance Current Processes

threading.Thread(target=start).start()
