from pymongo import MongoClient

# case "${TO_DBNAME}" in
#    "PERF") DBHOST_TO=10.62.101.61;; ##need to update to master node
#    "PRE") DBHOST_TO=10.62.109.137;;
#    "UAT") DBHOST_TO=10.62.109.137;;
#    "SIT") DBHOST_TO=10.62.109.136;;
# esac

ignoreList=['lenovo.com','yopmail.com','sharklasers.com']

client=MongoClient('mongodb://admin:L3novo@10.62.109.137:27017/')
db=client.UAT

collist=db.list_collection_names()
for _collection in collist:
    print(_collection)

client.close()