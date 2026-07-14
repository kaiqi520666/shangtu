class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    async def set(self, key, value, *, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        if ex is not None:
            self.expirations[key] = ex
        return True

    async def get(self, key):
        return self.values.get(key)

    async def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    async def expire(self, key, seconds):
        self.expirations[key] = seconds
        return True

    async def ttl(self, key):
        return self.expirations.get(key, -1)

    async def eval(self, _script, numkeys, key, window_seconds):
        assert numkeys == 1
        count = await self.incr(key)
        if await self.ttl(key) < 0:
            await self.expire(key, int(window_seconds))
        return count

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.expirations.pop(key, None)
        return len(keys)
