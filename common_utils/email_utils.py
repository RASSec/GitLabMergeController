import yaml
import os
import requests
import logging
import dateutil.parser

def strftime(data):

    d = dateutil.parser.parse(data)
    return d.strftime('%Y-%m-%d %H:%M:%S')


def getProjectStr(web_url):
    startStr = 'http://gitlab.xpaas.lenovo.com/'
    endStr='/merge_requests'
    startIndex = web_url.find(startStr)
    if startIndex>=0:
        startIndex += len(startStr)
    endIndex = web_url.find(endStr)
    return web_url[startIndex:endIndex]



def send_email(subject,content,to):

    #Read the config/merge_handle_rule.yaml
    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/common.yaml', 'r') as f:
        common = yaml.load(f.read())
        print(common)
        
    xMessageUrl = common['xMessageUrl']
    xMessageData =  common['xMessageData']
    xMessageHeaders = common['xMessageHeaders']
    # auditrecord = common['auditrecord']

    xMessageData['subject'] = subject
    xMessageData['content'] = content
    xMessageData['to'] = to
    # if to :
    #     xMessageData['to'] = to
    # else :
    #     xMessageData['to'] = auditrecord
        

    try:
        r = requests.post(url=xMessageUrl,headers=xMessageHeaders, json=xMessageData,verify=False)
        if r.json()['success']:
            print("Successfully sent email")
        return r.json()
    except Exception as e:
        logging.exception(e)
        print ("Error: unable to send email")


def gitlab_email(action,notification,mr,option):
    subject = ""
    content = "" 
    to = []
    if "aftermerge" in notification and "aftermerge" == action:
        projectName = getProjectStr(mr.web_url)
        subject = "gitlab autoMerge success"
        content = "<html> Project :"+projectName+"<body><a href="+mr.web_url+">   MR  </a> has merged from "+ mr.source_branch+ "  to    "+ mr.target_branch+ "   at    "+strftime(mr.merged_at )+"</body></html>"
        commits = mr.commits()
        for commit in commits:
            to.append(commit.committer_name+'@lenovo.com')
            print(commit)
        r = send_email(subject,content,to)
        if r['success']:
            mr.notes.create({'body': 'autoMerge success notification email has sent to committer'})
    elif "mergeconflict"in notification and "mergeconflict" == action:
        subject="gitlab  mergeconflict"
        to.append(mr.author["name"]+"@lenovo.com")
        content = "<html><body><a href="+mr.web_url+"> MR </a> has some mergeconflict  </body></html>"
        r = send_email(subject,content,to)
        if r['success']:
            mr.notes.create({'body': 'mergeconflict  notification email has sent'})
    elif "connotmerge"in notification and "connotmerge" == action:
        subject="gitlab autoMerge connotmerge"
        to.append(mr.author["name"]+"@lenovo.com")
        content = "<html><body><a href="+mr.web_url+"> MR </a> is unable to be accepted \
        (ie: Work in Progress, Closed, Pipeline Pending Completion, or Failed while requiring Success)</body></html>"
        r = send_email(subject,content,to)
        if r['success']:
            mr.notes.create({'body': 'connotmerge  notification email has sent'})
    elif "cherrypickfailed"in notification and "cherrypickfailed" == action:
        subject = "gitlab cherry-pick up failed"
        content = "<html><body>cherry-pick your commit: "+option.id+" in <a href="+mr.web_url+"/> MR </a> to develop branch failed </body></html>"
        to.append(option.committer_email)
        to.append("kongyi1@lenovo.com")
        r = send_email(subject,content,to)
        if r['success']:
            mr.notes.create({'body': 'cherrypick '+option.id+' failed and notification email has sent to '+option.committer_email})
    elif "cherrypicksuccess" == action:
        subject = "gitlab commit cherry-pick up success notification"
        content = "<html><body>cherry-pick your commit: "+option.id+" in <a href="+mr.web_url+"/> MR </a> to develop branch success </body></html>"
        to.append(option.committer_email)
        to.append("kongyi1@lenovo.com")
        r = send_email(subject,content,to)
        if r['success']:
            mr.notes.create({'body': 'cherrypick '+option.id+' success and notification email has sent to  '+option.committer_email})
    elif "reviewers" in notification and "reviewers" == action:
        subject = 'gitlab review'
        content = "<html><body>you are assigned as the reviewer for this"+"<a href="+mr.web_url+"> MR </a> </body></html>"
        r = send_email(subject,content,option)
        if r['success']:
            mr.notes.create({'body': 'reviewers  notification email has sent'})
    elif  'auditrecord' in notification and "auditrecord" == action:
        projectName = getProjectStr(mr.web_url)
        subject = 'gitlab auditrecord'
        content = "<html> Project :"+projectName+"<body><a href="+mr.web_url+">   MR  </a> has merged from "+ mr.source_branch+ "  to    "+ mr.target_branch+ "   at    "+strftime(mr.merged_at )+"</body></html>"
        to = option
        r = send_email(subject,content,to)
        # if r['success']:
        #     mr.notes.create({'body': 'autoMerge success notification email has sent to auditrecord'})
    else :
        print('No such action')

# if __name__ == '__main__':
#     gitlab_email(action,notification,mr,option=None)