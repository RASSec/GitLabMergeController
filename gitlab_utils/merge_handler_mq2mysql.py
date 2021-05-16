import pika
import time
import pymysql
import datetime
import json
import dateutil.parser
from sys import argv
import os
import sys

dirname, _ = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname+"/../common_utils")

globalParams={}

import configHandler as configer

def getCommitDate(dateStr):
    d = dateutil.parser.parse(dateStr)
    return(d.strftime('%Y-%m-%d-%H-%M-%S'))  # ==> '09/26/2008'

# You may ask why we declare the queue again ‒ we have already declared it in our previous code.
# We could avoid that if we were sure that the queue already exists. For example if send.py program
# was run before. But we're not yet sure which program to run first. In such cases it's a good
# practice to repeat declaring the queue in both programs.
# channel.queue_declare(queue='ky-exchange-fanout')

def callback(channel, method, properties, body):

    dbConfig = configer.ReadYaml(globalParams['configPath'], 'dataSource')

    time.sleep(1)
    print(" [x] Received %r" % body)
    #Here add the logic to query and insert data into mysql database.
    # 使用cursor()方法获取操作游标

    messageJson=json.loads(body)
    #print(messageJson)

    try:
        # 执行sql语句
        # 开启数据库
        db_conn = pymysql.connect(dbConfig['host'], dbConfig['user'], dbConfig['password'], dbConfig['db'])
        cursor = db_conn.cursor()

        _sql_exist="select * from gitlab_merge_request_state where mr_id='"+str(messageJson['mr_id'])+"' and mr_project_id='"+str(messageJson['mr_project_id'])+"'"

        cursor.execute(_sql_exist)
        queryResult=cursor.fetchone()

        _mr_title=(messageJson['mr_title']).replace("'","").replace('"',"")

        if queryResult !=None:
           print("do update sql")
           _sql_exec="UPDATE gitlab_merge_request_state SET mr_state='"+messageJson['mr_state']+"',mr_approvers='"+messageJson['mr_approver']+"',mr_updated_at='"+getCommitDate(messageJson['mr_updated_at'])+"',issue_key='"+messageJson['issue_key']+"', changefiles='"+messageJson['changefiles']+"', additionslines='"+messageJson['additionlines']+"', deletelines='"+messageJson['deletelines']+"' WHERE mr_id='"+str(messageJson['mr_id'])+"' and mr_project_id='"+str(messageJson['mr_project_id'])+"' "

        else:
            print("do insert sql")
            _sql_exec = "INSERT INTO gitlab_merge_request_state(mr_id,mr_title,mr_created_at,mr_target_branch,mr_source_branch,mr_project_id,mr_project_name,mr_state,mr_url,mr_rule,mr_approvers,mr_auther,mr_updated_at,issue_key,changefiles,additionslines,deletelines) VALUES('" + str(messageJson['mr_id']) + "', '" + \
                        _mr_title + "','" + getCommitDate(messageJson['mr_created_at']) + "','" + messageJson['mr_target_branch'] + "','" + messageJson['mr_source_branch'] + "','" + str(messageJson['mr_project_id']) + "','" + messageJson['mr_project_name'] + "','" + messageJson['mr_state'] + "','"+messageJson['mr_url']+"','"+messageJson['mr_rule']+"','"+messageJson['mr_approver']+"','"+messageJson['mr_auther']+"','"+getCommitDate(messageJson['mr_updated_at'])+"','"+messageJson['issue_key']+"','"+messageJson['changefiles']+"','"+messageJson['additionlines']+"','"+messageJson['deletelines']+"')"

        print(_sql_exec)
        cursor.execute(_sql_exec)
        db_conn.commit()
        cursor.close()
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(e)
    finally:
        db_conn.close()

def mergeHanlder_mq2mysql(configPath):

    configObj=configer.ReadYaml(configPath,'mq')

    globalParams['configPath']=configPath

    credentials = pika.PlainCredentials(configObj['user'], configObj['password'])
    mq_conn = pika.BlockingConnection(pika.ConnectionParameters(configObj['host'], int(configObj['port']), configObj['virtualhost'], credentials))
    channel = mq_conn.channel()

    try:
        # channel.basic_consume(callback,queue="QA",no_ack=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(configObj['queue'], callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    finally:
        mq_conn.close()

if __name__ == '__main__':
    _ ,configfile = argv

    if configfile == "None":

       configfile = dirname + "/../config/common.yaml"

       mergeHanlder_mq2mysql(configfile)



