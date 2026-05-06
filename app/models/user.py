import hashlib
from db import get_redis

r = get_redis()

class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = self._hash(password)
        self.notifications = 0

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def save(self):
        r.hset(f"user:{self.username}", mapping={
            "username": self.username,
            "password": self.password,
            "notifications": self.notifications
        })
        r.sadd("users", self.username)

    @staticmethod
    def find(username: str):
        return r.hgetall(f"user:{username}") or None

    @staticmethod
    def exists(username: str) -> bool:
        return r.exists(f"user:{username}") == 1

    @staticmethod
    def verify_password(username: str, password: str) -> bool:
        user = User.find(username)
        if not user:
            return False
        return user["password"] == hashlib.sha256(password.encode()).hexdigest()