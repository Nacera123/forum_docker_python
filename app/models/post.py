from db import get_redis

r = get_redis()

class Post:
    def __init__(self, content: str, author: str, forum_id: str):
        self.content = content
        self.author = author
        self.forum_id = forum_id
        self.likes = 0

    def save(self):
        pid = r.incr("post:id:counter")
        r.hset(f"post:{pid}", mapping={
            "id": pid,
            "content": self.content,
            "author": self.author,
            "forum_id": self.forum_id,
            "likes": self.likes
        })
        r.lpush(f"forum:{self.forum_id}:posts", pid)
        r.sadd(f"user:{self.author}:posts", pid)
        return pid

    @staticmethod
    def find(pid: str):
        return r.hgetall(f"post:{pid}") or None

    @staticmethod
    def find_by_forum(fid: str):
        pids = r.lrange(f"forum:{fid}:posts", 0, -1)
        posts = []
        for pid in pids:
            data = r.hgetall(f"post:{pid}")
            if data:
                posts.append(data)
        return posts

    @staticmethod
    def find_by_user(username: str):
        pids = r.smembers(f"user:{username}:posts")
        return [r.hgetall(f"post:{pid}") for pid in pids]

    @staticmethod
    def like(pid: str, username: str):
        already_liked = r.sismember(f"post:{pid}:likers", username)
        if already_liked:
            r.srem(f"post:{pid}:likers", username)
            r.hincrby(f"post:{pid}", "likes", -1)
            return False
        else:
            r.sadd(f"post:{pid}:likers", username)
            r.hincrby(f"post:{pid}", "likes", 1)
            return True

    @staticmethod
    def is_liked_by(pid: str, username: str) -> bool:
        return r.sismember(f"post:{pid}:likers", username)

    @staticmethod
    def get_likes(pid: str) -> int:
        return int(r.hget(f"post:{pid}", "likes") or 0)