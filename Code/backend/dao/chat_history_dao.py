from repository.chat_history_repository import ChatHistoryRepository


class ChatHistoryDAO:
    def __init__(self, repository: ChatHistoryRepository):
        self.repository = repository

    def get_chat_history(self, session_id: str, user_id: int = None):
        return self.repository.get_history(session_id, user_id)

    def save_chat_history(self, session_id: str, history: list, user_id: int, course_name: str = None, first_question: str = None):
        self.repository.save_history(session_id, history, user_id, course_name, first_question)

    def get_user_sessions(self, user_id: int):
        return self.repository.get_user_sessions(user_id)

    def get_user_sessions_by_course(self, user_id: int, course_name: str):
        return self.repository.get_user_sessions_by_course(user_id, course_name)

    def get_user_history_summary(self, user_id: int, limit: int = 50):
        return self.repository.get_user_history_summary(user_id, limit)

    def get_user_history_summary_by_course(self, user_id: int, course_name: str, limit: int = 50):
        return self.repository.get_user_history_summary_by_course(user_id, course_name, limit)

    def get_user_courses(self, user_id: int):
        return self.repository.get_user_courses(user_id)

    def delete_session(self, session_id: str, user_id: int):
        return self.repository.delete_session(session_id, user_id)
