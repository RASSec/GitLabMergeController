from datetime import datetime
import merge_handler as mh
from sys import argv
import time
from imp import reload
import os

dirname, _ = os.path.split(os.path.abspath(__file__))

# 每n秒执行一次
def timer(interval,configfile,cmdb,commonConfig):
    while True:
        reload(mh) #每次都重新加载一次，这样可以支持代码的热更新
        mh.set_globalParams('commConfigPath', commonConfig)
        mh.merge_handler(configfile,None)
        time.sleep(int(interval))  #通过定义sleep的时间实现扫描的间隔

_, interval,configfile, commonConfig = argv

if commonConfig == 'None':
    commonConfig = dirname + "/../config/common.yaml"

timer(interval,configfile,None,commonConfig)