import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions

# Initialize sentence-transformers embedding function
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

DB_DIR = "./chroma_db"

def get_chroma_collection(collection_name: str = "machine_manuals") -> chromadb.Collection:
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def index_chunks(chunks: List[Dict[str, Any]], collection_name: str = "machine_manuals") -> int:
    """
    Stores chunks with metadata into Chroma collection.
    """
    collection = get_chroma_collection(collection_name)
    
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"chunk_{i}_{chunk.get('manual', 'doc')}_{chunk.get('error_code', 'none')}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "machine": chunk.get("machine", "Unknown"),
            "model": chunk.get("model", "Unknown"),
            "manual": chunk.get("manual", ""),
            "section": chunk.get("section", ""),
            "error_code": chunk.get("error_code") or ""
        })

    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    return len(ids)

def search(query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Performs similarity search in Chroma collection.
    Returns top k chunks with similarity scores.
    """
    collection = get_chroma_collection("machine_manuals")

    where_clause = None
    if filter_metadata:
        # Construct Chroma where filter
        filters = []
        for key, val in filter_metadata.items():
            if val is not None:
                filters.append({key: {"$eq": val}})
        
        if len(filters) == 1:
            where_clause = filters[0]
        elif len(filters) > 1:
            where_clause = {"$and": filters}

    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where_clause
    )

    formatted_results = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)

        for doc, meta, dist in zip(docs, metas, distances):
            # For cosine distance in Chroma: lower distance = higher similarity.
            # Convert cosine distance to cosine similarity score: score = 1 - distance
            sim_score = max(0.0, 1.0 - dist)
            formatted_results.append({
                "text": doc,
                "machine": meta.get("machine"),
                "model": meta.get("model"),
                "manual": meta.get("manual"),
                "section": meta.get("section"),
                "error_code": meta.get("error_code") if meta.get("error_code") != "" else None,
                "score": sim_score,
                "distance": dist,
                "score_type": "similarity"
            })

    return formatted_results

query_store = search

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.ingest import load_and_chunk_manuals
    chunks = load_and_chunk_manuals()
    indexed_count = index_chunks(chunks)
    print(f"Indexed {indexed_count} chunks into Chroma DB.")

    print("\n--- Test Search 1: Overheating symptom ---")
    res1 = search("why is my motor overheating")
    for r in res1[:2]:
        print(f"Machine: {r['machine']} | Score: {r['score']:.4f} | Section: {r['section']}")

    print("\n--- Test Search 2: E101 with Press-200 filter ---")
    res2 = search("E101", filter_metadata={"machine": "Press-200"})
    for r in res2:
        print(f"Machine: {r['machine']} | Score: {r['score']:.4f} | Section: {r['section']}")
