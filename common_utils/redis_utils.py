# from rediscluster import StrictRedisCluster
# startup_nodes = [
#     {"host":"10.122.64.110", "port":7000},
#     {"host":"10.122.64.110", "port":7001},
#     {"host":"10.122.61.41", "port":7002},
#     {"host":"10.122.61.41", "port":7003},
#     {"host":"10.122.61.39", "port":7004},
#     {"host":"10.122.61.39", "port":7005}
# ]
# rc = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
# rc.set('name','admin')
# rc.set('age',18)
# print("name is: ", rc.get('name'))
# print("age  is: ", rc.get('age'))

import redis
import yaml
import os

'''
# 直连方式：这种连接是连接一次就断了，耗资源.
r = redis.Redis(host='10.122.64.110',port=8000)
r.set('project_id',123445)
print(r.get('name').decode('utf8'))
print("get name value is:")
print(r.get('project_id').decode('utf8'))
'''
'''
# 连接池方式：当程序创建数据源实例时，系统会一次性创建多个数据库连接，并把这些数据库连接保存在连接池中，当程序需要进行数据库访问时，无需重新新建数据库连接，而是从连接池中取出一个空闲的数据库连接
# '''

redisConn = None

def redisConnFactory():

    current_path = os.path.abspath(os.path.dirname(__file__))

    with open(current_path + '/../config/common.yaml', 'r') as f:
        common = yaml.load(f.read())
        print(common)
    redisConfig = common['redis']
    print(redisConfig)
    pool = redis.ConnectionPool(host=redisConfig['host'], port=redisConfig['port'], decode_responses=True,db=0)  # 实现一个连接池
    redisConn= redis.Redis(connection_pool=pool)

    return redisConn

redisConn=redisConnFactory()


def getRedisConn():
    global redisConn
    if redisConn == None:
        redisConn = redisConnFactory()

    return redisConn

def checkValueInRedisSet(redisConn,setName,value):


    if redisConn.sismember(setName, value):
        return True
    else:
        return False

def getRedisSetValue(redisConn,setName):

    _vals=redisConn.smembers(setName)
    print("========= "+ setName  +" ============")
    for _val in _vals:
        print(_val.decode('utf8'))
    print("===================================")


def deleteRedisSetValue(redisConn,setName,valueList):
    for _value in valueList:
       print("delete "+_value)
       redisConn.srem(setName, _value)


# def
#
# #r.set('name','root')
# r.sadd("set_name1","aa")
# r.sadd("set_name1","bb")
# r.sadd("set_name1","cc")
#
# if r.sismember("set_name1", "cc1"):
#     print("find the value in redis set")
# else:
#     print("not find the value in redis set")
#
# r.connection_pool.disconnect()

if __name__=="__main__":
    #getRedisSetValue(getRedisConn(),"unTrackMRSet")


    #delete unTrackMRSet
    # _vals = redisConn.smembers("unTrackMRSet")
    # for _val in _vals:
    #     print("delete "+_val)
    #     redisConn.srem("unTrackMRSet", _val)


    #deleteRedisSetValue(getRedisConn(), "unTrackMRSet", ['370','67184','32','31','518','425','401','405','35','176','548','1451','381'])
    #deleteRedisSetValue(getRedisConn(), "unTrackMRSet", ['6238-3128'])

    # delete hash set
    redis_conn = getRedisConn()
    api_test_result_dict = redis_conn.hgetall("apiTest")
    for api_test_result in api_test_result_dict:
        print(api_test_result)
        redis_conn.hdel('apiTest', api_test_result)