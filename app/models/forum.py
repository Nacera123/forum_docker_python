from db import get_redis

r = get_redis()

class Forum:
    def __init__(self, name: str, creator: str):
        self.name = name
        self.creator = creator
        self.nb_visite = 0

    def save(self):
        fid = r.incr("forum:id:counter")
        r.hset(f"forum:{fid}", mapping={
            "id": fid,
            "name": self.name,
            "creator": self.creator,
            "nb_visite": self.nb_visite
        })
        r.sadd("forums", fid)
        r.sadd(f"user:{self.creator}:forums", fid)
        return fid

    @staticmethod
    def find(fid: str):
        return r.hgetall(f"forum:{fid}") or None

    @staticmethod
    def all(sort='desc'):
        fids = r.smembers("forums")
        forums = []
        for fid in fids:
            data = r.hgetall(f"forum:{fid}")
            if data:
                data["nb_posts"] = r.llen(f"forum:{fid}:posts")
                forums.append(data)
        # Tri par nombre de visites
        reverse = sort == 'desc'
        forums.sort(key=lambda f: int(f.get('nb_visite', 0)), reverse=reverse)
        return forums

    @staticmethod
    def find_by_user(username: str):
        fids = r.smembers(f"user:{username}:forums")
        return [r.hgetall(f"forum:{fid}") for fid in fids]

    @staticmethod
    def increment_visite(fid: str):
        r.hincrby(f"forum:{fid}", "nb_visite", 1)