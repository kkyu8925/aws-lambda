import json
import boto3
import base64
import pymysql
from requests_toolbelt.multipart import decoder


def create_connection_token():
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
    secrets = create_connection_token()
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


def uploadToS3(body, originalFileName):
    s3 = boto3.client('s3')
    s3.put_object(
        ACL="public-read",
        Bucket='kkyu-sparta',
        Body=body,
        Key=originalFileName,
        ContentType='image/' + originalFileName.split('.')[1]
    )

    conn = db_ops()
    cursor = conn.cursor()
    cursor.execute("insert into image(url) value('" + originalFileName + "')")
    conn.commit()


def lambda_handler(event, context):
    if 'Content-Type' in event['headers']:
        content_type_header = event['headers']['Content-Type']
    else:
        content_type_header = event['headers']['content-type']

    postdata = base64.b64decode(event['body']).decode('iso-8859-1')

    lst = []
    for part in decoder.MultipartDecoder(postdata.encode('utf-8'), content_type_header).parts:
        lst.append(part.text)

    decoder_file = decoder.MultipartDecoder(postdata.encode('utf-8'), content_type_header)
    file_name = lst[1]  # 파일명은 한글이 아니어야 한다.
    uploadToS3(lst[0].encode('iso-8859-1'), file_name)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
        }),
    }