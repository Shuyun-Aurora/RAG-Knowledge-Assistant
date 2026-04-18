from pymongo import MongoClient
from datetime import datetime

class ChatHistoryRepository:
    def __init__(self, mongo_url: str, mongo_db: str):
        self.client = MongoClient(mongo_url)
        self.db = self.client[mongo_db]
        self.collection = self.db["chat_histories"]

    def get_history(self, session_id: str, user_id: int = None):
        """
        获取聊天历史记录
        :param session_id: 会话ID
        :param user_id: 用户ID，如果提供则验证会话属于该用户
        :return: 历史记录列表
        """
        query = {"session_id": session_id}
        if user_id is not None:
            query["user_id"] = user_id
            
        doc = self.collection.find_one(query)
        return doc["history"] if doc and "history" in doc else []

    def save_history(self, session_id: str, history: list, user_id: int, course_name: str = None, first_question: str = None):
        """
        保存聊天历史记录
        :param session_id: 会话ID
        :param history: 历史记录列表
        :param user_id: 用户ID
        :param course_name: 课程名称
        :param first_question: 第一条问题
        """
        update_data = {
            "history": history, 
            "user_id": user_id,
            "updated_at": datetime.utcnow()
        }
        
        # 添加课程名称字段
        if course_name:
            update_data["course_name"] = course_name
        
        # 如果是新会话，添加创建时间和第一条问题
        if first_question:
            update_data["created_at"] = datetime.utcnow()
            update_data["first_question"] = first_question
        
        self.collection.update_one(
            {"session_id": session_id},
            {"$set": update_data},
            upsert=True
        )

    def get_user_sessions(self, user_id: int):
        """
        获取用户的所有会话ID
        :param user_id: 用户ID
        :return: 会话ID列表
        """
        docs = self.collection.find({"user_id": user_id}, {"session_id": 1})
        return [doc["session_id"] for doc in docs]

    def get_user_sessions_by_course(self, user_id: int, course_name: str):
        """
        获取用户在指定课程下的所有会话ID
        :param user_id: 用户ID
        :param course_name: 课程名称
        :return: 会话ID列表
        """
        docs = self.collection.find(
            {"user_id": user_id, "course_name": course_name}, 
            {"session_id": 1}
        )
        return [doc["session_id"] for doc in docs]

    def get_user_history_summary(self, user_id: int, limit: int = 50):
        """
        获取用户的历史记录摘要，按时间倒序排列
        :param user_id: 用户ID
        :param limit: 返回记录数量限制
        :return: 历史记录摘要列表
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$project": {
                "session_id": 1,
                "first_question": 1,
                "created_at": 1,
                "updated_at": 1,
                "course_name": 1,
                "message_count": {"$size": "$history"}
            }},
            {"$sort": {"updated_at": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        return results

    def get_user_history_summary_by_course(self, user_id: int, course_name: str, limit: int = 50):
        """
        获取用户在指定课程下的历史记录摘要，按时间倒序排列
        :param user_id: 用户ID
        :param course_name: 课程名称
        :param limit: 返回记录数量限制
        :return: 历史记录摘要列表
        """
        pipeline = [
            {"$match": {"user_id": user_id, "course_name": course_name}},
            {"$project": {
                "session_id": 1,
                "first_question": 1,
                "created_at": 1,
                "updated_at": 1,
                "course_name": 1,
                "message_count": {"$size": "$history"}
            }},
            {"$sort": {"updated_at": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        return results

    def get_user_courses(self, user_id: int):
        """
        获取用户参与过的所有课程名称
        :param user_id: 用户ID
        :return: 课程名称列表
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$course_name"}},
            {"$project": {"course_name": "$_id"}},
            {"$sort": {"course_name": 1}}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        return [doc["course_name"] for doc in results if doc["course_name"]]

    def delete_session(self, session_id: str, user_id: int):
        """
        删除指定会话（仅限会话所有者）
        :param session_id: 会话ID
        :param user_id: 用户ID
        :return: 是否删除成功
        """
        result = self.collection.delete_one({"session_id": session_id, "user_id": user_id})
        return result.deleted_count > 0
