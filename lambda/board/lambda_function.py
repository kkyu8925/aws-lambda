import json
import boto3
import pymysql
from datetime import date
import math


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
    paramType = event['queryStringParameters']['type']
    conn = db_ops()
    cursor = conn.cursor()

    try:
        if paramType == 'write':
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
        elif paramType == 'list':
            paramWord = event['queryStringParameters']['word']
            paramCurrPage = event['queryStringParameters']['page']
            paramPerPage = event['queryStringParameters']['perPage']

            if paramCurrPage is None:
                paramCurrPage = 1

            if paramPerPage is None:
                paramPerPage = 10

            startPage = str((int(paramCurrPage) - 1) * int(paramPerPage))

            if not paramWord:
                cursor.execute("select count(idx) as count from bbs")
                count = cursor.fetchone()
                totalCount = int(count['count'])
                totalPage = math.ceil(totalCount / int(paramPerPage))
                cursor.execute("select idx, title, regDate from bbs limit " + startPage + "," + paramPerPage)
                result = cursor.fetchall()
            else:
                cursor.execute("select count(idx) as count from bbs  where title like '%" + paramWord + "%'")
                count = cursor.fetchone()
                totalCount = int(count['count'])
                totalPage = math.ceil(totalCount / int(paramPerPage))
                cursor.execute(
                    "select idx, title, regDate from bbs where title like '%" + paramWord + "%' limit " + startPage + "," + paramPerPage)

                result = cursor.fetchall()

            body = json.dumps({
                "result": "success",
                "data": {
                    "contents": result,
                    "pageOptions": {"perPage": paramPerPage, "totalPage": totalPage, "currPage": paramCurrPage,
                                    "totalCount": totalCount}
                }
            })
        elif paramType == 'read':
            idx = event['queryStringParameters']['idx']
            cursor.execute("select * from bbs where idx=" + idx)
            bbs = cursor.fetchone()
            body = json.dumps({
                "result": "success",
                "data": bbs
            })
        elif paramType == 'delete':
            idx = event['queryStringParameters']['idx']
            cursor.execute("delete from bbs where idx=" + idx)
            conn.commit()
            body = json.dumps({
                "message": "success",
            })
        elif paramType == 'deleteAll':
            idxs = event['queryStringParameters']['idxs']
            print(idxs)
            cursor.execute("delete from bbs where idx in(" + idxs + ")")
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
                'Access-Control-Allow-Methods': 'POST,GET,DELETE'
            },
            "body": body,
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            # Cross Origin처리
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,GET,DELETE'
            },
            "body": json.dumps({
                "message": "fail",
            }),
        }
