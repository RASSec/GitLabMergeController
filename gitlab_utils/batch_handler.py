import sys
import gitlab
import os
import yaml

def batch_crate_branch():

    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/batch_handler.yaml', 'r') as f: batch = yaml.load(f.read())

    batch_create_branch_infos   = batch['batch_create_branch_infos']

    for batch_create_branch_info in batch_create_branch_infos:
        project_id = batch_create_branch_info['project_id']
        branchNameList = batch_create_branch_info['branchNameList']
        refBranch = batch_create_branch_info['refBranch']
        branchNameListCopy =branchNameList.copy()

        gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
        project = gl.projects.get(project_id)
        for branchName in branchNameList:
            try:
                project.branches.create({'branch': branchName,'ref': refBranch})
                print(' Create branch success : ' +branchName)
                branchNameListCopy.remove(branchName)
            except Exception as e:
                if 400 == e.response_code:
                    print(' Branch already exists : ' + branchName )
                else :
                    print(e)
        if branchNameListCopy:
            print( str(branchNameListCopy)+ '  fail to  create ')
        else:
            print('batch branch create success ')


def batch_tag():
    
    current_path = os.path.abspath(os.path.dirname(__file__))
    with open(current_path + '/../config/batch_handler.yaml', 'r') as f: batch = yaml.load(f.read())

    batch_create_tag_infos =  batch['batch_create_tag_infos']

    for batch_create_tag_info in batch_create_tag_infos:
        tag_name = batch_create_tag_info['tag_name']
        refBranch = batch_create_tag_info['refBranch']
        project_id = batch_create_tag_info['project_id']
        msg = batch_create_tag_info['msg']

        gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
        project = gl.projects.get(project_id)

        try:
            project.tags.create( {'tag_name': tag_name , 'ref': refBranch, 'message': msg} )
            print(' Create tag success ,project : ' +str(project.name) +'   branch:  '+refBranch+  '  tag_name:  ' +tag_name)
        except Exception as e:
            print(str(e)+'  '+str(project.name) +'   branch:  '+refBranch+  '  tag_name:  ' +tag_name)
    
def batch_merge():

    current_path = os.path.abspath(os.path.dirname(__file__))
    with open(current_path + '/../config/batch_handler.yaml', 'r') as f: batch = yaml.load(f.read())

    batch_merge_infos =  batch['batch_merge_infos']

    for batch_merge_info in batch_merge_infos:

        project_id = batch_merge_info['project_id']
        source_branch = batch_merge_info['source_branch']
        target_branch = batch_merge_info['target_branch']
        title = batch_merge_info['title']
        
        gl = gitlab.Gitlab('http://gitlab.xpaas.lenovo.com', private_token='V13qjyLio-NDzEMYAUc9')
        project = gl.projects.get(project_id)
        
        try:
            mr = project.mergerequests.create({'source_branch': source_branch, 'target_branch': target_branch, 'title': title})
            mr.merge()
            print('batch merge success: '+'source_branch: '+source_branch+' target_branch: '+target_branch)
        except Exception as e:
            if 405 == e.response_code:
                print('MR is unable to be accepted'+'source_branch: '+source_branch+' target_branch: '+target_branch)
            elif 406 == e.response_code :
                print('MR has some merge conflicit'+'source_branch: '+source_branch+' target_branch: '+target_branch)
            elif 409 == e.response_code :
                print('Another open merge request already exists for this source branch: !148 '+'source_branch: '+source_branch+' target_branch: '+target_branch)
            else:
                print(e)
       
if __name__ == '__main__':
    # batch_tag()
    batch_crate_branch()
    # batch_merge()