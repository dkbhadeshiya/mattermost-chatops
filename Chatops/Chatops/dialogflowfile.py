import dialogflow_v2
from Chatops import config
import json
from google.protobuf.json_format import MessageToJson
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GOOGLE_APPLICATION_CREDENTIALS

client = dialogflow_v2.SessionsClient()

session = client.session_path(config.PROJECT_ID, config.SESSION_ID)


def call_dialogflow(message):

    query_input = {'text': {'text': message, 'language_code': 'en-US'}}

    response = client.detect_intent(session, query_input=query_input)

    res = json.loads(MessageToJson(response))

    dialogflow_response = {}

    if 'intent' in res['queryResult']:
        intent = res['queryResult']['intent']['displayName']
    else:
        intent = None

    dialogflow_response.update({'entities': res['queryResult']['parameters'],
                                'intent': intent,
                                'message': res['queryResult']['queryText']})

    return dialogflow_response

