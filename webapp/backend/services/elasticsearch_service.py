import logging
import asyncio
from elasticsearch import Elasticsearch

log = logging.getLogger(__name__)


class ElasticsearchService:
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client

    async def keep_alive(self):
        while True:
            try:
                self.es.info()
                await asyncio.sleep(1500)
            except Exception as e:
                log.error("Failed to keep ES alive: %s", e)
                await asyncio.sleep(5)
