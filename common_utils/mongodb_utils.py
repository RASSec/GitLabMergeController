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
collection=db.SmbUser
#collection=db.LoyaltyCustomerProfile
for item in collection.find():
    print(item)
# for item in collection.find(filter={"userId":{"$regex":".*@lenovo.com"}}):
#     print(item)

#cursor =collection.find(filter={"$or":[{"userId":{"$regex":".*@lenovo.com"}},{"userId":{"$regex":".*@yopmail.com"}},{"userId":{"$regex":".*@sharklasers.com"}}]})# Cursor

# here is the query to update first name
# condition = {"$nor":[{"userId":{"$regex":".*@lenovo.com"}},{"userId":{"$regex":".*@yopmail.com"}},{"userId":{"$regex":".*@sharklasers.com"}}]}
# result = collection.update_many(condition,{"$set":{"firstName":"****"}})
# print(result)

# here is the query to update last name
# condition = {"$nor":[{"userId":{"$regex":".*@lenovo.com"}},{"userId":{"$regex":".*@yopmail.com"}},{"userId":{"$regex":".*@sharklasers.com"}}]}
# result = collection.update_many(condition,{"$set":{"lastName":"****"}})
# print(result)


# here is to query to update userUid
# condition = {"$nor":[{"userId":{"$regex":".*@lenovo.com"}},{"userId":{"$regex":".*@yopmail.com"}},{"userId":{"$regex":".*@sharklasers.com"}}]}
# result = collection.update_many(condition,{"$set":{"userUid":"****"}})
# print(result)


#here is the sample data
#{'_id': ObjectId('5cbf3c704918e12caab7804b'), 'userId': 'johnn2019@icloud.com', 'country': 'US', 'firstName': 'psychic', 'lastName': 'chris', 'store': 'usweb', 'userStatus': 'Unchecked'}

#Final result
# {'_id': ObjectId('5cbf36e24918e12caab42d03'), 'userId': '***@mindspring.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'myperkspot', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf374e4918e12caab4769b'), 'userId': '***@gmail.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'usweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf37cc4918e12caab4d26b'), 'userId': '***@gmail.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'perksoffer', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf384c4918e12caab53426'), 'userId': '***@hotmail.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'usweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf38ad4918e12caab580fe'), 'userId': '***@yahoo.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'perksoffer', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf39274918e12caab5c2db'), 'userId': '***@gmail.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'usweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf392e4918e12caab5c839'), 'userId': '***@yahoo.co.jp', 'country': 'JP', 'firstName': '****', 'lastName': '****', 'store': 'jptvc', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf3bf94918e12caab73fdb'), 'userId': '***@grupocamarotti.com.br', 'country': 'BR', 'firstName': '****', 'lastName': '****', 'store': 'brweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf3c334918e12caab75e23'), 'userId': '***@unitybox.de', 'country': 'DE', 'firstName': '****', 'lastName': '****', 'store': 'deweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf3c4d4918e12caab76b32'), 'userId': '***@gmail.com', 'country': 'TW', 'firstName': '****', 'lastName': '****', 'store': 'twweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf3c704918e12caab7804b'), 'userId': '***@icloud.com', 'country': 'US', 'firstName': '****', 'lastName': '****', 'store': 'usweb', 'userStatus': 'Unchecked'}
# {'_id': ObjectId('5cbf3c7e4918e12caab786f2'), 'userId': '***@gmail.com', 'country': 'TW', 'firstName': '****', 'lastName': '****', 'store': 'twweb', 'userStatus': 'Unchecked'}

#here is the query to update the userId
# condition={"$nor":[{"userId":{"$regex":".*@lenovo.com"}},{"userId":{"$regex":".*@yopmail.com"}},{"userId":{"$regex":".*@sharklasers.com"}},{"userId":{"$regex":".*@test.com"}},{"userId":{"$regex":".*@leno.com"}}]}
# result =collection.update_many(condition,{"$set":{"userId":"****@customer.com"}})
# print(result)

# for i in cursor:
#     print(i)
#     if not cursor.alive:
#         break

# for i in cursor:
#     origin_id=i['userId']
#     suffix=(origin_id.split("@"))[1]
#     if not "***" in origin_id:
#        print(origin_id)
#        result = collection.update_one({'userId':origin_id}, {'$set': {'userId': '***@'+suffix}})
#     if not cursor.alive:
#         break
client.close()