from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from Chatops import run, config
import json
import pymysql
import sqlalchemy as db


@csrf_exempt
def index(request):
    data = json.loads(request.body)
    if 'build' in data:

        """connect mysql database"""
        connection_string = f'mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_URL}/{config.DB_NAME}'
        engine = db.create_engine(connection_string)
        connection = engine.connect()
        metadata = db.MetaData()

        """Get all user"""
        table_botuser = db.Table('user_botuser', metadata, autoload=True, autoload_with=engine)
        query_f = db.select([table_botuser.columns.channel_id])
        resultproxy = connection.execute(query_f)
        users = resultproxy.fetchall()

        build = data['build']
        project_name = build['project_name'].split('/')[-1]
        commit_id = build['commit_id']
        status = build['status']
        committer = build['committer']
        branch = build['branch']

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
                    "value": commit_id
                },
                {
                    "short": True,
                    "title": "Status",
                    "value": status
                },
                {
                    "short": True,
                    "title": "Committer",
                    "value": committer
                },
                {
                    "short": True,
                    "title": "Branch",
                    "value": branch
                }
            ],
        }]}

        for user in users:
            run.send_notification(user[0], props)

    return HttpResponse('')
