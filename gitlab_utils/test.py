import gitlab

client = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='QJ2Yu4q6f3rzKc5cjFAx')
client.auth()
project = client.projects.get("3128")
mrs = project.mergerequests.list(state='opened', order_by='updated_at',all=True)

for mr in mrs:
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    changes = mr.changes()
    print("there have total "+str(changes['changes_count'])+ " files changes in this MR")
    additions=0
    deletions=0

    commits = mr.commits()
    print("-------------------------------------------------------------------")
    for commit in commits:
        # print(commit)
        commitDetail=project.commits.get(commit.id)
        print(commitDetail)
        additions=additions+(commitDetail.stats)['additions']
        deletions=deletions+(commitDetail.stats)['deletions']
        print(str((commitDetail.stats)['additions'])+" "+str((commitDetail.stats)['deletions']))
        # statuses=commit.statuses.list()
        # # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # for statue in statuses:
        #     print(statue)
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("total new add line is: " + str(additions) + " total delete line is: " + str(deletions))
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")





