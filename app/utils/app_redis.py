import redis, os

# Redis connection configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Global Redis client
if os.environ.get("REDIS_URL"):
    redis_client = redis.from_url(os.environ["REDIS_URL"])
else:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


def get_redis():
    """
    Returns the global Redis client instance.

    :return: A Redis client instance.
    :rtype: redis.Redis
    """
    return redis_client
