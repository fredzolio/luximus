import os
import json
from typing import Optional, Dict
import redis.asyncio as redis


class FlowRepository:
    def __init__(self):
        self.redis = None

    async def init_redis(self):
        if not self.redis:
            self.redis = redis.from_url(
                url=self._construct_redis_url(),
                encoding='utf-8',
                decode_responses=True  # Decodifica automaticamente as respostas para strings
            )
            try:
                await self.redis.ping()
            except redis.ConnectionError as e:
                print(f"Erro ao conectar ao Redis: {e}")
                self.redis = None  # Reseta a conexão em caso de erro

    def _construct_redis_url(self) -> str:
        """
        Constrói a URL de conexão com o Redis com base nas variáveis de ambiente.
        """
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        db = os.getenv("REDIS_DB", "0")
        password = os.getenv("REDIS_PASSWORD", "")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"

    async def get_flow_state(self, flow_name: str, user_id: str) -> Optional[Dict]:
        await self.init_redis()
        if not self.redis:
            print("Redis não está conectado.")
            return None
        key = self._generate_key(flow_name, user_id)
        state = await self.redis.get(key)
        return json.loads(state) if state else None

    async def set_flow_state(self, flow_name: str, user_id: str, state: Dict, expire_seconds: int = 3600):
        await self.init_redis()
        if not self.redis:
            print("Redis não está conectado. Não foi possível definir o estado.")
            return
        key = self._generate_key(flow_name, user_id)
        await self.redis.set(key, json.dumps(state), ex=expire_seconds)

    async def delete_flow_state(self, flow_name: str, user_id: str):
        await self.init_redis()
        if not self.redis:
            print("Redis não está conectado. Não foi possível deletar o estado.")
            return
        key = self._generate_key(flow_name, user_id)
        await self.redis.delete(key)

    def _generate_key(self, flow_name: str, user_id: str) -> str:
        return f"flow:{flow_name}:{user_id}"

    async def close_redis(self):
        """
        Fecha a conexão com o Redis.
        """
        if self.redis:
            await self.redis.close()
            await self.redis.wait_closed()
            self.redis = None
            print("Conexão com o Redis foi fechada.")
