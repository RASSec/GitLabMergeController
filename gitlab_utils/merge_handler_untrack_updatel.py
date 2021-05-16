import pika
import time
import pymysql
import datetime
import json
import dateutil.parser
from sys import argv
import os
import sys
import gitlab

dirname, _ = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname+"/../common_utils")

globalParams={}

import configHandler as configer
import redis_utils as redis_utlis
import email_utils as email_utils
import mysql_utils as mysql_utils

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

    #Based on mr_id and project_id get MR status
    gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
    gl.auth()

    project = gl.projects.get(messageJson['project_id'],all=True)

    mr = project.mergerequests.get(messageJson['mr_id'])

    print(mr.state)

    #Then do the db update
    try:
        # 执行sql语句
        # 开启数据库

        db_conn = pymysql.connect(dbConfig['host'], dbConfig['user'], dbConfig['password'], dbConfig['db'])
        cursor = db_conn.cursor()

        _sql_exist="select * from gitlab_merge_request_state where mr_id='"+str(messageJson['mr_id'])+"' and mr_project_id='"+str(messageJson['project_id'])+"'"

        print(_sql_exist)
        cursor.execute(_sql_exist)
        queryResult=cursor.fetchone()

        if queryResult !=None:
            #_sql_exec="UPDATE gitlab_merge_request_state SET mr_state='"+messageJson['mr_state']+"',mr_approvers='"+messageJson['mr_approver']+"',mr_updated_at='"+getCommitDate(messageJson['mr_updated_at'])+"' WHERE mr_id='"+str(messageJson['mr_id'])+"'"
            _sql_exec = "UPDATE gitlab_merge_request_state SET mr_state='" + mr.state + "' WHERE mr_id='" + str(messageJson['mr_id']) + "' and mr_project_id='"+str(messageJson['project_id'])+"'"

        else:
             pass

        if mr.state =="merged" or mr.state =="closed" or mr.state =="cancelled":
            if mr.state == "merged":
                _sql_exec="UPDATE gitlab_merge_request_state SET mr_state='" + mr.state + "' , good_track='bad' WHERE mr_id='" + str(messageJson['mr_id']) + "' and mr_project_id='"+str(messageJson['project_id'])+"'"
            print("do update sql: "+_sql_exec)
            cursor.execute(_sql_exec)
            db_conn.commit()
            #here we need to send email to notify the auther his MR be merged under code review track
            if mr.state =="merged":
               sendAlertToUntrackMR(mr.author['username'],mr.web_url,mr.merged_by['username'])
               # record mr and comment info 
            # mysql_utils.merge_info_record(mr,None,'bad')
            mysql_utils.comment_info_record(mr)


        # remove the record in redis
        _valueList=[]
        #print(messageJson['mr_id']+"-"+messageJson['project_id'])
        _valueList.append(messageJson['mr_id']+"-"+messageJson['project_id'])
        print(_valueList)
        redis_utlis.deleteRedisSetValue(redis_utlis.getRedisConn(),"unTrackMRSet",_valueList)

        cursor.close()
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(e)
    finally:
        db_conn.close()


def sendAlertToUntrackMR(auther,mr_url,merger):

    alertEmailContent="""
    <html>
    <body>
    Hi AUTHER <br/><br/>

    You recived this email, because your <a href="MR_URL">merge request</a> be closed without follow code review process <br/><br/>

    For details, please refer <a href='https://kmdmz.xpaas.lenovo.com/display/EB/Code+Review+Specification+With+Auto+Merge+Handler'>Code Review Process</a>   
    </body>
    </html>
    """
    alertEmailContent=alertEmailContent.replace('AUTHER',auther).replace('MR_URL',mr_url)
    autherEmail=auther+"@lenovo.com"
    mergedByEmail=merger+"@lenovo.com"
    #emailLoop=[autherEmail,mergedByEmail,'kongyi1@lenovo.com','qinlang1@lenovo.com']
    emailLoop = ['kongyi1@lenovo.com', 'qinlang1@lenovo.com']
    #print(alertEmailContent)

    try:
        email_utils.send_email("Alert! Merge Request Be Merged Without Code Review",alertEmailContent,emailLoop)
    except Exception as e:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"-> merge_handler_undertrack_update->sendAlertToUnTrackMR: "+ e)

def mergeHanlder_untrack_update(configPath):

    configObj=configer.ReadYaml(configPath,'mq')

    globalParams['configPath']=configPath

    credentials = pika.PlainCredentials(configObj['user'], configObj['password'])
    mq_conn = pika.BlockingConnection(pika.ConnectionParameters(configObj['host'], int(configObj['port']), configObj['virtualhost'], credentials))
    channel = mq_conn.channel()

    try:
        #channel.basic_consume(callback,queue="QA",no_ack=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume("untrack-state-sync", callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    finally:
        mq_conn.close()

if __name__ == '__main__':
    _ ,configfile = argv

    if configfile == "None":

       configfile = dirname + "/../config/common.yaml"

       mergeHanlder_untrack_update(configfile)


    # < class 'gitlab.v4.objects.ProjectMergeRequest'> = > {'id': 70340, 'iid': 1451
    #
    # , 'project_id': 2899, 'title': 'Acct 4091 fix gbweb languagefallback', 'description': '', 'state': 'merged', 'created_at': '2019-11-22T12:18:32.270+08:00', 'updated_at': '2019-11-25T19:07:34.429+08:00', 'merged_by': {
    #     'id': 3411, 'name': 'wanglei60', 'username': 'wanglei60', 'state': 'active', 'avatar_url': None,
    #     'web_url': 'http://gitlab.xpaas.lenovo.com/wanglei60'}, 'merged_at': '2019-11-25T19:07:34.703+08:00', 'closed_by': None, 'closed_at': None, 'target_branch': 'develop', 'source_branch': 'ACCT-4091-fix-gbweb-languagefallback', 'user_notes_count': 1, 'upvotes': 0, 'downvotes': 0, 'assignee': None, 'author': {
    #     'id': 3411, 'name': 'wanglei60', 'username': 'wanglei60', 'state': 'active', 'avatar_url': None,
    #     'web_url': 'http://gitlab.xpaas.lenovo.com/wanglei60'}, 'assignees': [], 'source_project_id': 2899, 'target_project_id': 2899, 'labels': [], 'work_in_progress': False, 'milestone': None, 'merge_when_pipeline_succeeds': False, 'merge_status': 'can_be_merged', 'sha': 'ac0d6888efc5e25a2c1912fd5d37cca166d81127', 'merge_commit_sha': 'a5574464841c9c1c5f75e4d17dd0cdebe3f667fc', 'discussion_locked': None, 'should_remove_source_branch': None, 'force_remove_source_branch': False, 'reference': '!1451', 'web_url': 'http://gitlab.xpaas.lenovo.com/li-ecomm/li-ecomm-microservices/merge_requests/1451', 'time_stats': {
    #     'time_estimate': 0, 'total_time_spent': 0, 'human_time_estimate': None,
    #     'human_total_time_spent': None}, 'squash': False, 'task_completion_status': {'count': 0,
    #                                                                                  'completed_count': 0}, 'subscribed': False, 'changes_count': '27', 'latest_build_started_at': '2019-11-22T12:14:46.449+08:00', 'latest_build_finished_at': '2019-11-22T12:19:48.954+08:00', 'first_deployed_to_production_at': None, 'pipeline': {
    #     'id': 35484, 'sha': 'ac0d6888efc5e25a2c1912fd5d37cca166d81127', 'ref': 'ACCT-4091-fix-gbweb-languagefallback',
    #     'status': 'success',
    #     'web_url': 'http://gitlab.xpaas.lenovo.com/li-ecomm/li-ecomm-microservices/pipelines/35484'}, 'head_pipeline': {
    #     'id': 35484, 'sha': 'ac0d6888efc5e25a2c1912fd5d37cca166d81127', 'ref': 'ACCT-4091-fix-gbweb-languagefallback',
    #     'status': 'success',
    #     'web_url': 'http://gitlab.xpaas.lenovo.com/li-ecomm/li-ecomm-microservices/pipelines/35484',
    #     'before_sha': '6f394ae2a2a9b89365ef948904dc278fd74e9dec', 'tag': False, 'yaml_errors': None,
    #     'user': {'id': 3411, 'name': 'wanglei60', 'username': 'wanglei60', 'state': 'active', 'avatar_url': None,
    #              'web_url': 'http://gitlab.xpaas.lenovo.com/wanglei60'}, 'created_at': '2019-11-22T12:14:44.504+08:00',
    #     'updated_at': '2019-11-22T12:19:48.958+08:00', 'started_at': '2019-11-22T12:14:46.449+08:00',
    #     'finished_at': '2019-11-22T12:19:48.954+08:00', 'committed_at': None, 'duration': 297, 'coverage': None,
    #     'detailed_status': {'icon': 'status_success', 'text': 'passed', 'label': 'passed', 'group': 'success',
    #                         'tooltip': 'passed', 'has_details': True,
    #                         'details_path': '/li-ecomm/li-ecomm-microservices/pipelines/35484', 'illustration': None,
    #                         'favicon': '/assets/ci_favicons/favicon_status_success-8451333011eee8ce9f2ab25dc487fe24a8758c694827a582f17f42b0a90446a2.png'}}, 'diff_refs': {
    #     'base_sha': '0a0e221a9d55f5a84235f2ae903f504a5e331be7', 'head_sha': 'ac0d6888efc5e25a2c1912fd5d37cca166d81127',
    #     'start_sha': '0a0e221a9d55f5a84235f2ae903f504a5e331be7'}, 'merge_error': None, 'user': {'can_merge': True}}