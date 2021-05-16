import sys
import gitlab
import os
import yaml
import time


dirname, _ = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname+"/../common_utils")
from mysql_utils import *

def scan_mr():

    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"-> start scan merge request ")
    gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
    gl.auth()

    current_path = os.path.abspath(os.path.dirname(__file__))
    with open(current_path + '/../config/common.yaml', 'r') as f: scanrule = yaml.load(f.read())
    projectIds = scanrule['projectIds']

    for projectId in projectIds:
    
       project = gl.projects.get(projectId)
       projectName = project.name_with_namespace
       mrs = project.mergerequests.list(state='opened', order_by='updated_at',all=True)

       for mr in mrs:
           merge_info_record(mr,projectName)
       
if __name__ == '__main__':
    scan_mr()