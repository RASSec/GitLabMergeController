import consul
import re
import argparse
import time
from sys import argv

#https://python-consul.readthedocs.io/en/latest/

def findSubKey(parser_args):
    consul_client = consul.Consul(host="10.122.46.24", port="8500")
    #deployment/CICD/Release/
    _, keys = consul_client.kv.get(parser_args.rootpath, index=None, keys=True, separator=None)

    rootkey = keys[0]
    print(keys)
    child_key = keys[1:]

    candidate_keys = ['None']

    pattern = rootkey + "(.*?)/$"

    print(pattern)

    p = re.compile(pattern)

    for key in child_key:
        m=re.match(p, key)
        if m != None:
           candidate_keys.append(m.group(1))

    finalResult= candidate_keys

    if parser_args.returntype == "Str":
        finalResult = (parser_args.separator).join(candidate_keys)

    print(finalResult)

    return finalResult


def checkBranch(parser_args):

    consul_client = consul.Consul(host="10.122.46.24", port="8500")

    if parser_args.custom == "None" or parser_args.custom == parser_args.default:
            release=parser_args.default

    # call get default branch from default release
    else:
    # get default branch from custom release
          release=parser_args.custom

    try:
       _, branch = consul_client.kv.get("deployment/CICD/Release/" + release + "/branch", index=None, keys=None,separator=None)
    except Exception as e:
       print('None')
       return
    print(bytes.decode(branch['Value'])+",")
    return branch

def getGitRepo(parser_args):
    consul_client = consul.Consul(host="10.122.46.24", port="8500")

    if parser_args.jobname != "None":
      try:
          _, gitrepo = consul_client.kv.get("deployment/CICD/JenkinsJobs/" + parser_args.jobname + "/git_repo", index=None, keys=None,separator=None)
      except Exception as e:
         print('None')
         return
    else:
        gitrepo={}
        gitrepo['Value']="None"
    print(bytes.decode(gitrepo['Value']))
    return gitrepo

def getJobService(parser_args):
    consul_client = consul.Consul(host="10.122.46.24", port="8500")

    if parser_args.jobname != "None":
        try:
            _, jobService = consul_client.kv.get("deployment/CICD/JenkinsJobs/" + parser_args.jobname + "/service_list/"+parser_args.servicetype,index=None, keys=None, separator=None)
        except Exception as e:
            print('None')
            return
    else:
        jobService = {}
        jobService['Value'] = "None"
    print(bytes.decode(jobService['Value']))
    return jobService

def checkHybrisServerDeplooyStatus(parser_args):
    timeout=parser_args.timeout
    loopIndex=0
    totalSuccess = False
    while(True):
      loopIndex=loopIndex+1
      #print("start loop {index}".format(index=loopIndex))
      consul_client = consul.Consul(host="10.122.46.24", port="8500")
      # deployment/CICD/Release/
      _, keys = consul_client.kv.get(parser_args.keypath, index=None, keys=True, separator=None)

      for key in keys:
         try:
            _, value = consul_client.kv.get(key, index=None, keys=None, separator=None)
         except Exception as e:
            print('None')
         if bytes.decode(value['Value']) != "success":
             totalSuccess=False
             break
         else:
             totalSuccess=True
      if totalSuccess or (loopIndex > int(parser_args.timeout)):
         break
      time.sleep(60)

    if not totalSuccess:
        print("Failed")
        return
    print("Complete")
    return


Parser = argparse.ArgumentParser(add_help=True)
SubParsers = Parser.add_subparsers(help='Sub Commands')
ConsulKey_Parser = SubParsers.add_parser('consul_getkeys', help='this command used to list all keys in consul')
ConsulKey_Parser.add_argument('-rootpath',type=str,default='deployment',help='the rootpath in consul for list the keys')
ConsulKey_Parser.add_argument('-returntype',type=str,default='list',help='specify return type list or str')
ConsulKey_Parser.add_argument('-separator',type=str,default=',',help='if return as str, use separator to separate item')
ConsulKey_Parser.set_defaults(func=findSubKey)

CheckBranch_Parser = SubParsers.add_parser('check_branch', help='this command used to check current branch')
CheckBranch_Parser.add_argument('-default',type=str,default='None',help='specify defualt binding release')
CheckBranch_Parser.add_argument('-custom',type=str,default='None',help='specify custom  release')
CheckBranch_Parser.set_defaults(func=checkBranch)

GetGitRepo_Parser = SubParsers.add_parser('get_gitrepo', help='this command used to get jenkins job repo')
GetGitRepo_Parser.add_argument('-jobname',type=str,default='None',help='specify jenkins job name')
GetGitRepo_Parser.set_defaults(func=getGitRepo)

GetJobServiceList_Parser = SubParsers.add_parser('get_jobservice', help='this command used to get jenkins job servcie')
GetJobServiceList_Parser.add_argument('-jobname',type=str,default='None',help='specify jenkins job name')
GetJobServiceList_Parser.add_argument('-servicetype',type=str,default='values',help=' values and default, values include all values, default specify which should be select')
GetJobServiceList_Parser.set_defaults(func=getJobService)

GetHybrisDeployStatus_Parser = SubParsers.add_parser('get_hybrisSevStatus', help='this command used to get hybris server deploy status')
GetHybrisDeployStatus_Parser.add_argument('-env',type=str,default='preu',help='specify target environment')
GetHybrisDeployStatus_Parser.add_argument('-timeout',type=str,default='30',help='this value specify the default timeout (mins) setting ')
GetHybrisDeployStatus_Parser.add_argument('-keypath',type=str,default='',help='this value specify the key path to find the hybris server deployment status')
GetHybrisDeployStatus_Parser.set_defaults(func=checkHybrisServerDeplooyStatus)

if __name__=="__main__":
  args = Parser.parse_args()
  args.func(args)