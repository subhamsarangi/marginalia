import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions

DB_NAME = "marginalia"
CONTAINER_NAME = "enrichments"

_container = None


def _get_container():
    global _container
    if _container is None:
        client = CosmosClient(os.environ["COSMOS_URI"], os.environ["COSMOS_KEY"])
        db = client.create_database_if_not_exists(DB_NAME)
        _container = db.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/paper_id"),
        )
    return _container


def save_enrichment(paper_id: str, enrichment: dict):
    doc = {"id": paper_id, "paper_id": paper_id, **enrichment}
    _get_container().upsert_item(doc)


def get_enrichment(paper_id: str) -> dict | None:
    try:
        return _get_container().read_item(item=paper_id, partition_key=paper_id)
    except exceptions.CosmosResourceNotFoundError:
        return None
