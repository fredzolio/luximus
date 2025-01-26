import aioredis
import os
import json
from typing import Optional, Dict

class FlowRepository:
    def __init__(self):
        self.redis = None

    async def init_redis(self):
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(
                (os.getenv("REDIS_HOST", "localhost"), int(os.getenv("REDIS_PORT", 6379))),
                password=os.getenv("REDIS_PASSWORD", None),
                db=int(os.getenv("REDIS_DB", 0)),
                encoding='utf-8'
            )

    async def get_flow_state(self, flow_name: str, user_id: str) -> Optional[Dict]:
        await self.init_redis()
        key = self._generate_key(flow_name, user_id)
        state = await self.redis.get(key)
        return json.loads(state) if state else None

    async def set_flow_state(self, flow_name: str, user_id: str, state: Dict, expire_seconds: int = 3600):
        await self.init_redis()
        key = self._generate_key(flow_name, user_id)
        await self.redis.set(key, json.dumps(state), expire=expire_seconds)

    async def delete_flow_state(self, flow_name: str, user_id: str):
        await self.init_redis()
        key = self._generate_key(flow_name, user_id)
        await self.redis.delete(key)

    def _generate_key(self, flow_name: str, user_id: str) -> str:
        return f"flow:{flow_name}:{user_id}"
