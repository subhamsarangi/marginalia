import os
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

COLLECTION_NAME = "marginalia"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _get_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )


def _get_embeddings():
    from langchain_community.embeddings import FastEmbedEmbeddings
    return FastEmbedEmbeddings(model_name=EMBED_MODEL)


def push_chunks(chunks: list[dict]):
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    QdrantVectorStore.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=_get_embeddings(),
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        collection_name=COLLECTION_NAME,
    )
