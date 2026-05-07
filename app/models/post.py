from db import get_redis, get_pubsub_client
import json

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
        
        # Publier la notification sur Pub/Sub
        notification = {
            "post_id": pid,
            "forum_id": self.forum_id,
            "author": self.author,
            "content": self.content[:50] + "..." if len(self.content) > 50 else self.content
        }
        pubsub_client = get_pubsub_client()
        pubsub_client.publish(f"forum:{self.forum_id}:new_post", json.dumps(notification))
        
        # Aussi stocker dans une queue pour polling
        r.lpush(f"forum:{self.forum_id}:new_posts_queue", json.dumps(notification))
        r.ltrim(f"forum:{self.forum_id}:new_posts_queue", 0, 9)  # Garder les 10 derniers
        
        # Marquer comme non lu pour tous les autres utilisateurs
        Post.add_unread_for_all_users(self.forum_id, str(pid), self.author)
        
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

    @staticmethod
    def get_unread_count(forum_id: str, username: str) -> int:
        """Compte les posts non lus dans un forum pour un utilisateur"""
        unread = r.llen(f"forum:{forum_id}:new_posts_queue:unread:{username}")
        return unread

    @staticmethod
    def mark_forum_as_read(forum_id: str, username: str):
        """Marque tous les posts d'un forum comme lus pour un utilisateur"""
        r.delete(f"forum:{forum_id}:new_posts_queue:unread:{username}")

    @staticmethod
    def add_unread_for_all_users(forum_id: str, post_id: str, excluding_user: str):
        """Ajoute un post non lu pour tous les utilisateurs sauf l'auteur"""
        all_users = r.smembers("users")
        for username in all_users:
            if username != excluding_user:
                r.lpush(f"forum:{forum_id}:new_posts_queue:unread:{username}", post_id)