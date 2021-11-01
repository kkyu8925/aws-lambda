import json
import boto3
import pymysql
from datetime import date


def get_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="ap-northeast-2"
    )
    get_secret_value_response = client.get_secret_value(
        SecretId='rds-secret-01'
    )
    token = get_secret_value_response['SecretString']
    return eval(token)


def db_ops():
    secrets = get_secret()

    try:
        connection = pymysql.connect(
            host=secrets['host'],
            user=secrets['username'],
            password=secrets['password'],
            db='sparta',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    except pymysql.MySQLError as e:
        print("connection error!!")
        return e

    print("connection ok!!")
    return connection


def lambda_handler(event, context):
    conn = db_ops()
    cursor = conn.cursor()

    try:
        type = event['queryStringParameters']['type']

        if type == 'write':
            if event['httpMethod'] == 'OPTIONS':
                body = json.dumps({
                    "message": "success",
                })
            else:
                today = date.today()
                body = json.loads(event['body'])

                cursor.execute("insert into bbs(title, content, regDate) value('" + body['title'] + "', '" + body[
                    'content'] + "', '" + today.strftime("%Y%m%d") + "')")
                conn.commit()
                body = json.dumps({
                    "message": "success",
                })
        elif type == 'list':
            paramWord = event['queryStringParameters']['word']

            if not paramWord:
                cursor.execute("select idx, title, regDate from bbs")
                result = cursor.fetchall()
            else:
                cursor.execute("select idx, title, regDate from bbs where title like '%" + paramWord + "%'")
                result = cursor.fetchall()

            body = json.dumps({
                "result": "success",
                "data": result
            })
        elif type == 'read':
            idx = event['queryStringParameters']['idx']

            cursor.execute("select * from bbs where idx=" + idx)
            bbs = cursor.fetchone()

            body = json.dumps({
                "result": "success",
                "data": bbs
            })
        elif type == 'delete':
            idx = event['queryStringParameters']['idx']

            cursor.execute("delete from bbs where idx=" + idx)
            conn.commit()

            body = json.dumps({
                "message": "success",
            })
        return {
            "statusCode": 200,
            # Cross Origin처리
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": body,
        }
    except:
        return {
            "statusCode": 500,
            # Cross Origin처리
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,GET'
            },
            "body": json.dumps({
                "message": "fail",
            }),
        }
