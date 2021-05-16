import consul
import re
import time
from sys import argv

#https://python-consul.readthedocs.io/en/latest/

#curl -i http://10.122.46.24:8500/v1/kv/deployment/hybris?keys
#curl -i http://10.122.46.24:8500/v1/kv/deployment/hybris?keys

def getKVConsulHttp(rootpath,keys=False):
    pass



def checkHybrisServerDeplooyStatus(parser_args):
    timeout=parser_args.timeout
    loopIndex=0
    totalSuccess = False
    while(True):
      loopIndex=loopIndex+1
      print("start loop {index}".format(index=loopIndex))
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

if __name__=="__main__":

    serviceDict = {}
    c = consul.Consul(host='10.122.46.24', port='8500', token=None, scheme='http', verify=False)
    latestTag_FromRelease = c.kv.get('deployment/CICD/DockerImageBuild/dit/', index=None, recurse=True,
                                     wait=None,
                                     token=None, consistency=None,
                                     keys=False, separator='/', dc=None)

    print(latestTag_FromRelease)

    # ('58432', [{'LockIndex': 0, 'Key': 'deployment/CICD/DockerImageBuild/r20200311/DemoServiceA', 'Flags': 0,
    #             'Value': b'r20200311-ade93e4-20200226061910', 'CreateIndex': 280, 'ModifyIndex': 58432},
    #            {'LockIndex': 0, 'Key': 'deployment/CICD/DockerImageBuild/r20200311/DemoServiceB', 'Flags': 0,
    #             'Value': b'r20200311-ade93e4-20200225052104', 'CreateIndex': 281, 'ModifyIndex': 51231},
    #            {'LockIndex': 0, 'Key': 'deployment/CICD/DockerImageBuild/r20200311/DemoServiceC', 'Flags': 0,
    #             'Value': b'r20200311-ade93e4-20200225052104', 'CreateIndex': 51080, 'ModifyIndex': 51232},
    #            {'LockIndex': 0, 'Key': 'deployment/CICD/DockerImageBuild/r20200311/DemoServiceD', 'Flags': 0,
    #             'Value': b'r20200311-ade93e4-20200225052104', 'CreateIndex': 51081, 'ModifyIndex': 51233}])

    for service_tag in latestTag_FromRelease[1]:
     if service_tag['Key'].rindex('/')+1 != len(service_tag['Key']):
        serverName = service_tag['Key'][service_tag['Key'].rindex('/') + 1:]
        if serverName in serviceDict:
            serviceDict[serverName]['latest_tag'] = bytes.decode(service_tag['Value'])
        else:
            serviceDict[serverName] = {
                'current_tag': '',
                'latest_tag': bytes.decode(service_tag['Value']),
                'pre_tag': '',
                'update_status': "new service haven't deploy",
                'deploy_time': ''
            }
    print(serviceDict)