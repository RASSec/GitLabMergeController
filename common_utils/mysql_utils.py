import yaml
import os
import logging
import dateutil.parser
import pymysql

#this method based on project_id to query
def get_mrstate_by_project(project_id,state="NonMerge"):
    # Read the config/merge_handle_rule.yaml
    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/common.yaml', 'r') as f:
        common = yaml.load(f.read())
        print(common)

    dataSource = common['dataSource']
    try:
        db = pymysql.connect(dataSource['host'], dataSource['user'], dataSource['password'], dataSource['db'])
        cursor = db.cursor()

        if state=="NonMerge":
             _sql_exec = "select * from gitlab_merge_request_state where mr_project_id='"+project_id+"' and mr_state!='merged' and mr_state!='closed' and mr_state!='cancelled'"

        else:
             _sql_exec = "select * from gitlab_merge_request_state where mr_project_id='"+project_id+"' and mr_state='merged'"

        print(_sql_exec)

        cursor.execute(_sql_exec)

        _records=cursor.fetchall()

    finally:
       db.close()

    return _records

def trans_to_list_by_index(query_result,index=0):
    _new_list=[]

    for _item in query_result:
        _new_list.append(_item[index])

    return _new_list
        

def comment_info_record(mr):

    # Read the config/merge_handle_rule.yaml
    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/common.yaml', 'r') as f:
        common = yaml.load(f.read())
        print(common)

    dataSource = common['dataSource']

    notes = mr.notes.list(all=True)

    db = pymysql.connect(dataSource['host'], dataSource['user'],dataSource['password'], dataSource['db'])
    cursor = db.cursor()
    for note in notes:
        if note:
            if False == note.system  and note.author['name'] != 'Ecomm Git Maintainer' and  note.author['name'] !='jenkinsnemo' and 'reviewer:' not in note.body:
                try:
                    comment_id = note.id
                    mr_id = mr.iid
                    mr_web_url = mr.web_url
                    issue_key = strSplit(mr.title,'[',']')
                    target_branch = mr.target_branch
                    comment_created_at = strftime(note.created_at)
                    comment_update_at = strftime(note.updated_at)
                    comment_auther = note.author['name']
                    comment_body = pymysql.escape_string(note.body)
                    print(note)

                    commentSql = "INSERT INTO `DataAggregation`.`gitlab_merge_request_comment` ( `comment_id`, `mr_id`,`mr_web_url`,`issue_key`,`target_branch`, `comment_created_at`, `comment_update_at`, `comment_auther`, `comment_body` )\
                    VALUES ('%s', '%s','%s','%s','%s', '%s', '%s', '%s', '%s') \
                    ON DUPLICATE KEY UPDATE  mr_id ='%s', mr_web_url ='%s', issue_key='%s',target_branch='%s',comment_created_at ='%s', comment_update_at ='%s',comment_auther ='%s' ,comment_body = '%s' "%\
                    (comment_id,mr_id,mr_web_url,issue_key,target_branch,comment_created_at,comment_update_at,comment_auther,comment_body,mr_id,mr_web_url,issue_key,target_branch,comment_created_at,comment_update_at,comment_auther,comment_body)
                    
                    print(commentSql)

                    cursor.execute(commentSql)
                    db.commit()

                except Exception as e:
                    print(e)
                    print("ERROR: COMMENT INSERT INTO MYSQL ERROR")
        
    db.close()



def merge_info_record(mr,approvers,good_track):
    
    #Read the config/merge_handle_rule.yaml
    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/common.yaml', 'r') as f:
        common = yaml.load(f.read())
        print(common)
    
    dataSource = common['dataSource']

    mrsql = mr_sql(mr,approvers,good_track)

    db = pymysql.connect(dataSource['host'], dataSource['user'],dataSource['password'], dataSource['db'])
    cursor = db.cursor()

    try:
        cursor.execute(mrsql)
        db.commit()
    except Exception as e:
        print(e)
        print("ERROR: MergeRuests INSERT INTO  MYSQL ERROR")

    comment_info_record(mr)

    db.close()        


def mr_sql(mr,approvers,good_track):

    if approvers:
        approversStr = pymysql.escape_string(str(approvers))
    else:
        approversStr = ''
    mergeId = mr.iid
    issue_key = strSplit(mr.title,'[',']')
    project_id = mr.project_id
    project_name = strSplit(mr.web_url,'http://gitlab.xpaas.lenovo.com/','/merge_requests')
    merge_title = pymysql.escape_string( mr.title)
    description= mr.description
    state = mr.state
    created = strftime(mr.created_at)
    updated_at = strftime(mr.updated_at)
    merged_by = None 
    if None != mr.merged_by and 'name' in mr.merged_by:
        merged_by = mr.merged_by['name']
    merged_at =  strftime(mr.merged_at)
    closed_by = ''
    if None != mr.closed_by and 'username' in mr.closed_by: 
        closed_by = mr.closed_by['username']
    closed_at = mr.closed_at
    target_branch = mr.target_branch
    source_branch = mr.source_branch
    author = mr.author['name']
    web_url = mr.web_url
    merge_status = mr.merge_status
    assigneesName = []
    for assignee in mr.assignees:
        if None != assignee and 'name' in assignee:
            assigneesName.append(assignee['name'])
    assigneesNameStr = pymysql.escape_string(str(assigneesName))
    mrsql = "INSERT INTO `gitlab_merge_data`(mergeId,project_id,project_name,issue_key,merge_title,approvers,description,state,created,updated_at,merged_by,\
                merged_at,closed_by,closed_at,target_branch,source_branch,author,web_url,merge_status,assigneesName,good_track) \
                VALUES ('%s', '%s','%s','%s',  '%s', '%s','%s', '%s','%s', '%s','%s', '%s', '%s', '%s','%s', '%s','%s', '%s', '%s', '%s', '%s') \
                ON DUPLICATE KEY UPDATE \
                issue_key='%s',merge_title='%s',approvers='%s',description='%s',state='%s',updated_at='%s',merged_by='%s',\
                merged_at='%s',closed_by='%s',closed_at='%s',merge_status='%s',assigneesName='%s',good_track='%s'"% \
                (mergeId,project_id,project_name,issue_key,merge_title,approversStr,description,state,created,updated_at,merged_by,
                    merged_at,closed_by,closed_at,target_branch,source_branch,author,web_url,merge_status,assigneesNameStr,good_track,
                    issue_key,merge_title,approversStr,description,state,updated_at,merged_by,merged_at,closed_by,closed_at,merge_status,assigneesNameStr,good_track)
    
    print(mrsql)
    return mrsql


def commit_info_record(mr):
    mergeId = mr.iid
    commits = mr.commits()
    for cm in commits:
        commitId = cm.id
        issue_key = strSplit(cm.title,'[',']')
        created =  strftime(cm.created_at)
        commit_title = cm.title
        message = cm.message
        committer = cm.committer_name
        committer_email =cm.committer_email
        cmsql = "INSERT INTO `gitlab_auto_merge_commit_data`(commitId,issue_key,mergeId,created,commit_title,message,committer,committer_email) \
            VALUES ('%s', '%s','%s', '%s', '%s', '%s','%s','%s') \
             ON DUPLICATE KEY UPDATE  issue_key ='%s', mergeId ='%s', commit_title ='%s' ,message = '%s' "%\
            (commitId,issue_key,mergeId,created,commit_title,message,committer,committer_email,
                issue_key , mergeId , commit_title  ,message)
        print(cmsql)
        return cmsql


def strSplit(title,startStr,endStr):
  
    startIndex = title.find(startStr)
    if startIndex>=0:
        startIndex += len(startStr)
    endIndex = title.find(endStr)
    return title[startIndex:endIndex]

def GetJIRAID(title, startStr, endStr):
    jira_ids=strSplit(title,startStr,endStr)
    return jira_ids

def strftime(data):
    if data:
        d = dateutil.parser.parse(data)
        return d.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return data


# if __name__ == '__main__':
#     records=get_mrstate_by_project('6482',"NonMerge")
#     trans_to_list_by_index(records,0)
#     # for _record in records:
#     #     print(_record)