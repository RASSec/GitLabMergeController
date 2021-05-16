import sys
import gitlab
import os
import yaml
import time
from sys import argv
import re
import requests
import pika
import json


dirname, _ = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname+"/../common_utils")

globalParams={}

def set_globalParams(key,value):
    globalParams[key]=value

from email_utils import *
from mysql_utils import *
from rabbitmq_utils import *
import configHandler as configer
from redis_utils import *

#This is the unit object used to store the merge request status.
class mergeState(object):
    def __init__(self, mr, state , mr_rule, project):
        self.mr = mr
        self.state = state
        self.mr_rule = mr_rule
        self.approvers="None"
        self.issue_key=""
        self.project=project
        self.changefiles=0
        self.additionline=0
        self.deleteline=0

    def generateMQJson(self):
        #this method will genereate Json string and store in MQ
        # print("===============")
        # print(self.mr)
        # print(self.state)
        # print(self.mr_rule)
        # print("===============")
        #here need to add logic to get changefiles / additions / delete three parameters
        mrchange=self.mr.changes()
        self.changefiles=str(mrchange['changes_count'])

        commits = self.mr.commits()
        if commits != None:
          print("-------------------------------------------------------------------")
          for commit in commits:
            # print(commit)
            commitDetail = self.project.commits.get(commit.id)
            print(commitDetail)
            self.additionline = self.additionline + (commitDetail.stats)['additions']
            self.deleteline = self.deleteline + (commitDetail.stats)['deletions']
            print(str((commitDetail.stats)['additions']) + " " + str((commitDetail.stats)['deletions']))
          print("total new add line is: " + str(self.additionline) + " total delete line is: " + str(self.deleteline))

        mqJson={
             "mr_id": self.mr.iid,
             "mr_title": self.mr.title,
             "mr_created_at": self.mr.created_at,
             "mr_updated_at": self.mr.updated_at,
             "mr_target_branch": self.mr.target_branch,
             "mr_source_branch": self.mr.source_branch,
             "mr_project_id": self.mr.project_id,
             "mr_project_name": self.mr_rule['projectName'],
             "mr_auther": self.mr.author['name'],
             "mr_approver": self.approvers,
             "mr_state": self.state,
             "mr_url": self.mr.web_url,
             "mr_rule": self.mr_rule['mode'],
             "issue_key": self.issue_key,
             "changefiles": str(self.changefiles),
             "additionlines": str(self.additionline),
             "deletelines": str(self.deleteline)
        }

        return json.dumps(mqJson)

    def updateState(self,state):
        self.state=state
        return self

    def updateIssueKey(self,issuekey):
        self.issue_key=issuekey
        return self

    def setApprover(self,approvers):
        self.approvers=approvers

def syncMRStatus(mr_state):
    _mrstate_message=mr_state.generateMQJson()
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> sync merge status to MQ: " + _mrstate_message)

    configObj=configer.ReadYaml(globalParams['commConfigPath'],'mq')

    credentials = pika.PlainCredentials(configObj['user'], configObj['password'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(configObj['host'], int(configObj['port']), configObj['virtualhost'], credentials))

    # initial producer object
    producer = OneTimeProducer(connection=connection,
                               exchange=configObj['exchange'],
                               routing_key=configObj['route_key'])
    producer.sendMessage(_mrstate_message)
    connection.close()

def syncMRUnTrackStatus(mr_state):
    _mrstate_message = json.dumps(mr_state)

    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> sync merge status to MQ: " + _mrstate_message)

    configObj = configer.ReadYaml(globalParams['commConfigPath'], 'mq')

    credentials = pika.PlainCredentials(configObj['user'], configObj['password'])
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(configObj['host'], int(configObj['port']), configObj['virtualhost'], credentials))

    # initial producer object
    producer = OneTimeProducer(connection=connection,
                               exchange=configObj['exchange'],
                               routing_key='untrack-sync')
    producer.sendMessage(_mrstate_message)
    connection.close()


def assigneeControlMode(mr,merge_rule,approver, gl, project):

    mrstate= mergeState(mr,"Pending",merge_rule,project)  # When start the detect MR, this ojbect used to record the MR status
    mrstate.setApprover(','.join(approver))

    mrstate.updateIssueKey(GetJIRAID(mr.title, '[', ']'))

    compilePassFlag = False
    notification = merge_rule['notification']
    auditrecord = merge_rule['auditrecord']
    issuekey_valid = False

    copy_approver = approver.copy()
    if mr.assignee == None or mr.assignee['username'] not in copy_approver:
        if merge_rule['mode'] == 'assigneeControl' or merge_rule['mode'] == 'mixControl':
            print(copy_approver[0])
            user = gl.users.list(username=copy_approver[0])[0]
            print(user.id)
            mr.assignee_id = user.id
            mr_note = mr.notes.create({'body': copy_approver[0] + ' are assigned as the reviewer for this MR'})
            mr.save()

    # IF the MR in the handle scope, we need to handle this MR
    notes = mr.notes.list(all=True)

    for note in notes:
        if "Jenkins Build SUCCESS" in note.body:
             compilePassFlag = True
             break
        if "Issue Key is valid on JIRA" in note.body:
            issuekey_valid = True

    if merge_rule["compilepass"]:
        if not compilePassFlag:
           print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"-> waiting compile passs for merge request: "+ str(mr.iid))
           syncMRStatus(mrstate.updateState("waiting compile passs"))
           return
        else:
           print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + "-> compile pass for merge request: " + str(mr.iid))

    if 'jiraid_verify' in merge_rule:
        if merge_rule["jiraid_verify"]:
            if not issuekey_valid:
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> waiting correct issue_key: " + str(mr.iid))
                syncMRStatus(mrstate.updateState("waiting correct issue_key"))
                return
            else:
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "->  get valid issue_key: " + str(mr.iid))


    # handle by assigneeControl mode
    for note in notes:
        print(note)
        if (note.author)['name'] in approver:
            if merge_rule['approvalWord'] in note.body:
                copy_approver.remove((note.author)['name'])
                if len(copy_approver) == 0:
                    try:
                        if merge_rule['automerge']:
                           mr.notes.create({'body': 'This merge request has been approved by all reviewer'})
                           mr.merge()
                           syncMRStatus(mrstate.updateState("merged"))
                           comment_info_record(mr)
                           #merge_info_record(mr,approvers,'good')
                           gitlab_email('aftermerge',notification,mr,None)
                           gitlab_email('auditrecord',notification,mr,auditrecord)
                           # do commit cherry-pick
                           if merge_rule['cherry-pick']['enable'] and merge_rule['cherry-pick']['targetbranch'] != None:
                               commits = mr.commits()
                               revert_commits = []
                               # print("------- revert commit from old to new -----------")
                               for commit in commits:
                                   print(commit)
                                   revert_commits.insert(0, commit)
                                   # print("-----------------------")
                               for commit in revert_commits:
                                   print(commit)
                                   try:
                                          commit.cherry_pick(branch=merge_rule['cherry-pick']['targetbranch'])
                                          gitlab_email('cherrypicksuccess', notification, mr, commit)
                                   except Exception as e:
                                           print(e)
                                           print("cherry-pick commit " + commit.id + " to branch cherry-pick failed")
                                           gitlab_email('cherrypickfailed',notification,mr,commit)
                        return True
                    except Exception as e:
                        print(e.response_code)
                        if 405 == e.response_code:
                            # print("detect merge conflicit for MR")
                            # Send email notification
                            print("MR is unable to be accepted")
                            gitlab_email('connotmerge',notification,mr,None)
                        if 406 == e.response_code :
                            print("MR has some merge conflicit ")
                            gitlab_email('mergeconflict',notification,mr,None)
                    break
    if merge_rule['mode'] == 'assigneeControl' and len(copy_approver) != 0:
        # print(copy_approver[0])
        if mr.assignee == None or mr.assignee['name'] != copy_approver[0]:
            mr.notes.create({'body': copy_approver[0] + ' are assigned as the reviewer for this MR'})
            user = gl.users.list(username=copy_approver[0])[0]
            mr.assignee_id = user.id
            mr.save()
    syncMRStatus(mrstate.updateState("Waiting " + copy_approver[0] + " approve"))
    return False

def freeApproverCountMode(mr,merge_rule,approver, gl, project):

    mrstate = mergeState(mr, "Pending", merge_rule,project)  # When start the detect MR, this ojbect used to record the MR status

    mrstate.updateIssueKey(GetJIRAID(mr.title, '[', ']'))

    notes = mr.notes.list(all=True)
    reviewers=[]
    approvers=[]
    eMailreceivers = []
    emailSendFlag = False
    compilePassFlag = False
    notification = merge_rule['notification']
    auditrecord = merge_rule['auditrecord']
    issuekey_valid = False

    for note in notes:
        #print(note)
        if "reviewer:" in note.body:
            reviewers.extend(note.body.split(" ")[1:])
            mrstate.setApprover(','.join(reviewers))
            continue
        if merge_rule['approvalWord'] in note.body:
            if (note.author)['name'] not in approvers:
                   approvers.append((note.author)['username'])
        if "reviewers  notification email has sent" in note.body:
            emailSendFlag = True

        if "Jenkins Build SUCCESS" in note.body:
             compilePassFlag = True

        if "Issue Key is valid on JIRA" in note.body:
            issuekey_valid = True
             
    if 'defaultReviewers' in merge_rule:
        defaultReviewers = merge_rule['defaultReviewers']
        complementReviewers = []
        reviewersComments = ''

        for defaultReviewer in defaultReviewers:
            if '@'+defaultReviewer not in reviewers:
                complementReviewers.append('@'+defaultReviewer)
                reviewersComments += '@' +defaultReviewer+'  '
            
        if complementReviewers:
            reviewers.extend(complementReviewers)
            mr.notes.create({'body': 'reviewer:  ' + reviewersComments })

    if merge_rule["compilepass"]:
        if not compilePassFlag:
           print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> waiting compile passs for merge request: " + str(mr.iid))
           syncMRStatus(mrstate.updateState("waiting compile passs"))
           return
        else:
            print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + "-> compile passs for merge request: " + str(mr.iid))

    if 'jiraid_verify' in merge_rule:
        if merge_rule["jiraid_verify"]:
            if not issuekey_valid:
                print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + "-> waiting correct issue_key: " + str(mr.iid))
                syncMRStatus(mrstate.updateState("waiting correct issue_key"))
                return
            else:
                print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + "->  get valid issue_key: " + str(mr.iid))

    #copy_approvers = approvers.copy()
    if reviewers:
        copy_reviewers = reviewers.copy()
        #print(reviewers)
        #print(approvers)
        for reviewer in reviewers:
            print(reviewer[1:])
            eMailreceivers.append(reviewer[1:].strip()+"@lenovo.com")
            if reviewer[1:] in approvers:
                print("reviewer: "+reviewer+" approved")
                copy_reviewers.remove(reviewer)

        if len(copy_reviewers) != 0:
            # here need to add logic to clean ''
            copy_reviewers=list(reviewer for reviewer in copy_reviewers if reviewer!='')

        if len(copy_reviewers) == 0 and len(reviewers)!=0:

            try:
                if merge_rule['automerge']:
                   if "" in merge_rule['notification']:
                     mr.notes.create({'body': 'This merge request has been approved by all reviewer'})
                   mr.merge()
                   
                   #merge_info_record(mr,approvers)
                   syncMRStatus(mrstate.updateState("merged"))
                   print("autoMerge success")
                   comment_info_record(mr)
                   #merge_info_record(mr,approvers,'good')
                   gitlab_email('aftermerge',notification,mr,None)
                   gitlab_email('auditrecord',notification,mr,auditrecord)
                   # do commit cherry-pick
                   if merge_rule['cherry-pick']['enable'] and merge_rule['cherry-pick']['targetbranch'] != None:
                        commits = mr.commits()
                        revert_commits=[]
                        #print("------- revert commit from old to new -----------")
                        for commit in commits:
                            revert_commits.insert(0,commit)
                        #print("-----------------------")
                        for commit in revert_commits:
                            print(commit)
                            try:
                              commit.cherry_pick(branch=merge_rule['cherry-pick']['targetbranch'])
                              gitlab_email('cherrypicksuccess', notification, mr, commit)
                            except Exception as e:
                                print(e)
                                gitlab_email('cherrypickfailed',notification,mr,commit)
                                print("cherry-pick commit "+commit.id+" to branch cherry-pick failed")
            except Exception as e:
                print(e.response_code)
                if 405 == e.response_code:
                    print("MR is unable to be accepted")
                    gitlab_email('connotmerge',notification,mr,None)
                if 406 == e.response_code :
                    print("MR has some merge conflicit ")
                    gitlab_email('mergeconflict',notification,mr,None)
            return True
        if not emailSendFlag:
             gitlab_email('reviewers',notification,mr,eMailreceivers)
             emailSendFlag = True

        mrstate.updateState("waiting "+",".join(copy_reviewers)+" approve")

    else:
        mrstate.updateState("waiting set peer reviewer")

    syncMRStatus(mrstate)
    return False

        # Send email notification
        #1. based on the auth to get Approval count. based on the auth
        #2. Find the reviewer: setting to define the approval condition

#filterUnTrackMR(merge_rule['projectID'],mrs)
def filterUnTrackMR(projectID,opened_merges):
    # 1. 调用方法返回对应project下面的非Merge状态的记录
    # 2. 比较现在查询到的open状态的记录
    # 3. 如果在数据库中是非merge状态，但是在新的open状态中没有，则发送消息到特殊处理队列

    _non_merged=get_mrstate_by_project(projectID,"NonMerge")
    _non_merged_id_list=trans_to_list_by_index(_non_merged,0)
    _copy_non_merged_id_list=_non_merged_id_list.copy()

    for _merge in opened_merges:
       if str(_merge.iid) in _non_merged_id_list:
            _copy_non_merged_id_list.remove(str(_merge.iid))
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> filterUnTrackMR -> find untracked mr: " + ",".join(_copy_non_merged_id_list))
    #增加redis缓存，如果缓存里面还存在同样的MR_ID,就不发消息，如果不存在redis缓存的话就发消息，暂时一旦发现就发到消息队列中处理


    for _untrack_mr_id in _copy_non_merged_id_list:
        _message={
            "mr_id": _untrack_mr_id,
            "project_id": projectID,
            "action": "resync_mr_statue",
            "update_time": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        }

        # check if the untrack mr id in reids unTrackMRSet, then ignore, else send the untrack sync message and set the value in redis unTrackMRset
        if not checkValueInRedisSet(getRedisConn(), "unTrackMRSet", _untrack_mr_id+"-"+projectID):
               syncMRUnTrackStatus(_message)
               getRedisConn().sadd("unTrackMRSet",_untrack_mr_id+"-"+projectID)
        else:
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> filterUnTrackMR -> find untracked mr "+_untrack_mr_id+" in project "+ projectID +" in redis catch, ingore send sync untrack message")


def mixControlMode(mr,merge_rule,approver, gl, project):

     merge_rule['automerge'] = False
     if freeApproverCountMode(mr, merge_rule, approver, gl,project):
        print("freeApproverCoujntmode return True")
        merge_rule['automerge']=True
        assigneeControlMode(mr, merge_rule, approver, gl,project)

#define method and mode mapping
merge_handle_methods={'assigneeControl':assigneeControlMode, 'freeApproverCount':freeApproverCountMode, 'mixControl':mixControlMode}

def merge_handler(configfile,cmdb):
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"-> start scan merge request ")
    #gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
    gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='QJ2Yu4q6f3rzKc5cjFAx')
    gl.auth()

    ##Read the config/merge_handle_rule.yaml
    # 1. Gothrough the group one by one to get the project
    current_path = os.path.abspath(os.path.dirname(__file__))
    #print(current_path)
    #print(current_path + '/../config/merge_handle_rule.yaml')

    default_conf=current_path + '/../config/merge_handle_rule.yaml'

    if configfile == None:
        configfile = default_conf

    with open(configfile, 'r',encoding='utf8') as f:
         merge_rules = yaml.load(f.read())
         #print(merge_rules)

#    with open(current_path + '/../config/common.yaml', 'r') as f:
#        common = yaml.load(f.read())
#        print(common['baseUrl'])
#        print(common['xMessageHeaders'])
#        print(common['xMessageHeaders'])

    #groups = gl.groups.get("li-ecomm-account")

    # here need to add logic to read the project from rule configuration file.

    for merge_rule in merge_rules:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> check merge request for project: "+merge_rule['projectName'])
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> using handler mode： " + merge_rule['mode'])
        project = gl.projects.get(merge_rule['projectID'])
        approver=merge_rule['reviewer']
        # print(merge_rule['projectID'])
        # print(merge_rule['projectName'])
        # print(merge_rule['targetbranch'])
        # print(merge_rule['sourcebranch'])
        # print(merge_rule['notification'])
        # print(merge_rule['reviewer'])

        mrs = project.mergerequests.list(state='opened', order_by='updated_at',all=True)

        # SyncUnTrackStatue: Add logic to based on target project to get all un-merged MR-- Using Redis ?
        # query based on the mr_id and project_id
        # SyncUnTrackStatue: detect UnTracked MR and send it to MQ
        filterUnTrackMR(merge_rule['projectID'],mrs)

        for mr in mrs:

           # {'id': 117057, 'iid': 6820, 'project_id': 3128, 'title': 'WIP: Release/r20200526', 'description': '',
           #  'state': 'opened', 'created_at': '2020-05-06T18:03:02.760+08:00',
           #  'updated_at': '2020-05-07T13:53:10.048+08:00', 'merged_by': None, 'merged_at': None, 'closed_by': None,
           #  'closed_at': None, 'target_branch': 'release/R20200526', 'source_branch': 'release/R20200526',
           #  'user_notes_count': 0, 'upvotes': 0, 'downvotes': 0, 'assignee': None,
           #  'author': {'id': 2286, 'name': 'wenbw1', 'username': 'wenbw1', 'state': 'active', 'avatar_url': None,
           #             'web_url': 'http://gitlab.xpaas.lenovo.com/wenbw1'}, 'assignees': [], 'source_project_id': 3134,
           #  'target_project_id': 3128, 'labels': [], 'work_in_progress': True, 'milestone': None,
           #  'merge_when_pipeline_succeeds': False, 'merge_status': 'can_be_merged',
           #  'sha': '8b67ad85379e1ea05078fd295bb187440dbafa91', 'merge_commit_sha': None, 'squash_commit_sha': None,
           #  'discussion_locked': None, 'should_remove_source_branch': None, 'force_remove_source_branch': None,
           #  'allow_collaboration': False, 'allow_maintainer_to_push': False, 'reference': '!6820',
           #  'web_url': 'http://gitlab.xpaas.lenovo.com/li-ecomm/liecomm-hybris/merge_requests/6820',
           #  'time_stats': {'time_estimate': 0, 'total_time_spent': 0, 'human_time_estimate': None,
           #                 'human_total_time_spent': None}, 'squash': False,
           #  'task_completion_status': {'count': 0, 'completed_count': 0}, 'has_conflicts': False,
           #  'blocking_discussions_resolved': True}

           #   merge_info_record(mr,None)
           if mr.merge_status !="can_be_merged":
               continue

           if merge_rule['sourceproject_id_list'] != None:
               if mr.source_project_id not in merge_rule['sourceproject_id_list']:
                   continue

           if merge_rule['targetbranch'] != None:
               if mr.target_branch != merge_rule['targetbranch']:
                   if merge_rule['regularmatchbranch']:
                        if re.match(merge_rule['targetbranch'], mr.target_branch) !=None:
                            pass
                        else:
                            continue
                   else:
                       continue

           # If sourcebranch in merge rule is None, that means any MR from any source branch will be handle
           if merge_rule['sourcebranch'] != None:
               if mr.source_branch != merge_rule['sourcebranch']:
                   if merge_rule['regularmatchbranch']:
                       if re.match(merge_rule['sourcebranch'], mr.source_branch) !=None:
                           pass
                       else:
                           continue
                   else:
                       continue

           #here to add MR title filter
           if mergeTitleFilter(mr,merge_rule):
               # here need to detect if add comments, if no comments, will add it
               addNotes(mr,"Please fill in JRIA ticket ID as format [JIRAID] in merge request title")
               continue

           print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "-> start handler merge request： " + str(mr.iid))

           merge_handle_methods[merge_rule['mode']](mr, merge_rule, approver, gl, project)

    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"-> finish scan merge request")

def mergeTitleFilter(mr,merge_rule):
    # 1. if target branch name same as source branch name or highligh title with sync_code:
    if mr.target_branch == mr.source_branch or "Sync Code" in mr.title or "revert" in mr.title:
       return False
    # 2. reguler express to defect if there have JIRA ID

    #jiraid_RE = ".*(\[([A-Z]{3,}[0-9]{0,}-[0-9]{1,})(,[A-Z]{3,}[0-9]{0,}-[0-9]{1,})*\]).*"
    # change the jiraid_re for match special project id like [LEROW3-1] Bug fix test
    jiraid_RE = ".*(\[([A-Z]{3,}[0-9]{0,}-[0-9]{1,})(,[A-Z]{3,}[0-9]{0,}-[0-9]{1,})*\]).*"
    matchObj = re.match(jiraid_RE, mr.title)
    if matchObj != None:
       issuekey_ids = matchObj.group(1).replace("[", "").replace("]", "").split(",")

       #before return false we need to double check the JIRA ID to see if it is valide,
       #if valide, will return fasle
       #if invalide, will return true

       #Here need to add switch to enable or disable the ID check on JIRA
       if 'jiraid_verify' in merge_rule:
         if merge_rule['jiraid_verify']:
               if checkJIRAID(issuekey_ids):
                   #print("issue key is valid")
                   #here need to add logic to check if the key words alreasy exist
                   #mr.notes.create({'body': 'issue key is valid'})
                   addNotes(mr, 'Issue Key is valid on JIRA', checkDuplicate=True)
               else:
                   #here need to add logic to send email notification
                   # here need to add logic to check if the key words alreasy exist
                   #mr.notes.create({'body': 'issue key is not valid'})
                   addNotes(mr, 'Issue Key is not valid JIRA', checkDuplicate=True)
       return False

    return True

def addNotes(mr,comment,checkDuplicate=True):
    if checkDuplicate:
        notes = mr.notes.list(all=True)
        for note in notes:
            if comment in note.body:
                return
    mr.notes.create({'body': comment})
    return


def checkJIRAID(id_group):
    from jira import JIRA

    authPar = ('kongyi1', 'Diet5coke@')

    jiraServer = 'https://jira.xpaas.lenovo.com'

    jira = JIRA(basic_auth=authPar, options={'server': jiraServer, 'verify': False, })

    for jira_id in id_group:
        # jqlstring  = """project in ( 'SHOPE','ACCT','BROWSE','COMM','CONTENT')  AND issuekey='DCG-288' """
        jqlstring = "issuekey=" + jira_id
        try:
            query = jira.search_issues(
                jql_str=jqlstring,
                json_result=True,
                fields="cf[10403],cf[10004],fixVersion,cf[11712],cf[11415],type,status,key,assignee,created,updated",
                maxResults=40000)
            if query:
                pass
        except Exception as e:
            return False
    return True

if __name__ == '__main__':
    _ ,configfile, comm_config = argv

    if comm_config == 'None':
      globalParams['commConfigPath']=dirname+"/../config/common.yaml"
    else:
      globalParams['commConfigPath']=comm_config

    merge_handler(configfile,None)