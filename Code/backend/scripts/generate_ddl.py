import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import Base
from entity.User import User
from entity.Course import Course
from entity.Exercise import Exercise
from entity.ExerciseSet import ExerciseSet
from entity.Post import Post
from entity.Comment import Comment

def generate_ddl():
    # 获取所有表的DDL
    ddl = []
    
    # 创建数据库
    ddl.append("CREATE DATABASE IF NOT EXISTS tutoring_system;")
    ddl.append("USE tutoring_system;")
    ddl.append("")
    
    # 从SQLAlchemy模型生成DDL
    for table in Base.metadata.sorted_tables:
        ddl.append(str(table.compile()).strip() + ";")
        ddl.append("")  # 空行分隔
    
    # 写入文件
    with open('database_schema.sql', 'w') as f:
        f.write('\n'.join(ddl))
    
    print("DDL has been generated to database_schema.sql")

if __name__ == "__main__":
    generate_ddl() 