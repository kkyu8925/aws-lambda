import json
import boto3
import pymysql
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
    conn = db_ops()
    cursor = conn.cursor()

    try:
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

        return {
            "statusCode": 200,
            # Cross Origin처리
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE'
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
                'Access-Control-Allow-Methods': 'GET'
            },
            "body": json.dumps({
                "message": "fail",
            }),
        }
