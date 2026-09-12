import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions

DB_NAME = "marginalia"
CONTAINER_NAME = "rubrics"

_client = None
_container = None


def _get_container():
    global _client, _container
    if _container is None:
        _client = CosmosClient(os.environ["COSMOS_URI"], os.environ["COSMOS_KEY"])
        db = _client.create_database_if_not_exists(DB_NAME)
        _container = db.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/paper_id"),
        )
    return _container


def save_rubric(paper_id: str, rubric: dict):
    container = _get_container()
    doc = {"id": paper_id, "paper_id": paper_id, **rubric}
    container.upsert_item(doc)


def get_rubric(paper_id: str) -> dict | None:
    container = _get_container()
    try:
        return container.read_item(item=paper_id, partition_key=paper_id)
    except exceptions.CosmosResourceNotFoundError:
        return None
