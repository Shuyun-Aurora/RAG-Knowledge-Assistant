from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class UserAuth(Base):
    __tablename__ = "user_auth"

    user_id = Column("id", Integer, ForeignKey("user.id"), primary_key=True)
    hashed_password = Column("password", String)

    user = relationship("User", backref="auth", uselist=False)
