import json
import boto3
import pymysql


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
    body = json.loads(event['body'])
    conn = db_ops()
    cursor = conn.cursor()
    cursor.execute("insert into board(title, content) value('" + body['title'] + "', '" + body['content'] + "')")
    conn.commit()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
        }),
    }
