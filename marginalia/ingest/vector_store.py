import os
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "marginalia"
EMBEDDING_DIM = 1536


def _get_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.environ["GITHUB_TOKEN"],
        base_url=os.environ["GITHUB_MODELS_BASE_URL"],
    )


def ensure_collection():
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def push_chunks(chunks: list[dict]):
    ensure_collection()
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    store = QdrantVectorStore.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=_get_embeddings(),
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        collection_name=COLLECTION_NAME,
    )
    return store
