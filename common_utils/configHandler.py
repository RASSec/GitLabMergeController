import yaml
import os

current_path = os.path.abspath(os.path.dirname(__file__))
default_conf=current_path + '/../config/merge_handle_rule.yaml'

def ReadYaml(configPath,root=None):

    print("get configPath: "+configPath)

    if configPath == None:
        configfile = default_conf

    with open(configPath, 'r',encoding='utf8') as f:
         yaml_config = yaml.load(f.read())

    if root==None:
        resp = yaml_config
    else:
       resp= yaml_config[root]

    return resp
