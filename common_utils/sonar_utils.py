# from sonarqube_api import SonarAPIHandler
#
# h = SonarAPIHandler(user='kongyi1', password='Diet4coke@', host='sonar.xpaas.lenovo.com', port='80',base_path="/sonar")
#
#
# for project in h.get_resources_full_data(metrics=['coverage', 'violations']):
#     print(project)

#This is my sonarqube token:  316ffcee0f5cef7c3a6732f022f04870722bd63e
#This is a good guide: https://blog.csdn.net/LANNY8588/article/details/103496546

#1. use http://sonar.xpaas.lenovo.com/sonar/api/authentication/login with user/passowrd with Get method
# after send the reques can find the Authorization value in head   we can try to use this Authorization: Basic a29uZ3lpMTpEaWV0NGNva2VA directly

#2. use http://sonar.xpaas.lenovo.com/sonar/api/components/search_projects?filter=tags%20IN%20(li-ecomm-core)