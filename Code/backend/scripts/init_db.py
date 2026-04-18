import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from config.db import engine, Base
from entity.User import User
from entity.Course import Course
from entity.Exercise import Exercise
from entity.ExerciseSet import ExerciseSet
from entity.Post import Post
from entity.Comment import Comment

def init_database():
    # 1. 创建数据库
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password"
    )
    cursor = mydb.cursor()
    
    # 创建数据库（如果不存在）
    cursor.execute("CREATE DATABASE IF NOT EXISTS tutoring_system")
    cursor.close()
    mydb.close()
    
    # 2. 创建所有表
    Base.metadata.create_all(engine)
    
    print("Database and tables created successfully!")

if __name__ == "__main__":
    init_database() 