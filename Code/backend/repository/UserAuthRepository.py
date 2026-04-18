from sqlalchemy.orm import Session
from entity.UserAuth import UserAuth

def create_user_auth(db: Session, user_id: int, hashed_password: str):
    auth = UserAuth(user_id=user_id, hashed_password=hashed_password)
    db.add(auth)

def get_auth_by_user_id(db: Session, user_id: int):
    return db.query(UserAuth).filter(UserAuth.user_id == user_id).first()

def save_user_auth(db: Session, auth: UserAuth):
    db.add(auth)
    db.commit()
    db.refresh(auth)
