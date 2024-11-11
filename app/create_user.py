from pymongo import MongoClient
from bson import ObjectId
import os

# 连接到MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.quant_platform
    
    # 创建测试用户
    user = {
        '_id': ObjectId(),  # 生成唯一ID
        'username': 'test',
        'password': 'test',  # 实际应用中应使用密码哈希
        'strategy_ids': []
    }
    
    # 检查用户是否已存在
    existing_user = db.users.find_one({'username': 'test'})
    if existing_user:
        print("用户 'test' 已存在!")
    else:
        result = db.users.insert_one(user)
        print(f"创建用户成功! 用户ID: {result.inserted_id}")
    
    # 显示所有用户
    print("\n当前所有用户:")
    for user in db.users.find():
        print(f"用户名: {user['username']}, ID: {user['_id']}")

except Exception as e:
    print(f"发生错误: {e}")
finally:
    client.close()