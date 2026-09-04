import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions

# Initialize sentence-transformers embedding function
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

DB_DIR = "./chroma_db"

_CACHED_MACHINES: Optional[List[str]] = None

def invalidate_machines_cache():
    """Invalidates the in-memory cached machine list."""
    global _CACHED_MACHINES
    _CACHED_MACHINES = None

def get_chroma_collection(collection_name: str = "machine_manuals") -> chromadb.Collection:
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def reset_collection(collection_name: str = "machine_manuals") -> chromadb.Collection:
    """Deletes and re-creates collection for a clean indexing run."""
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    invalidate_machines_cache()
    return client.create_collection(
        name=collection_name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"}
    )

def index_chunks(chunks: List[Dict[str, Any]], collection_name: str = "machine_manuals") -> int:
    """
    Stores chunks with metadata into Chroma collection using upsert.
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
            "page": str(chunk.get("page") or ""),
            "error_code": chunk.get("error_code") or ""
        })

    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    invalidate_machines_cache()
    return len(ids)

def upsert_chunks(chunks: List[Dict[str, Any]], collection_name: str = "machine_manuals") -> int:
    """
    Upserts chunks into Chroma and invalidates the in-memory machine cache.
    """
    return index_chunks(chunks, collection_name=collection_name)

def delete_by_machine(machine_name: str, collection_name: str = "machine_manuals") -> int:
    """
    Removes all chunks for a given machine from the Chroma collection.
    Returns the count of deleted chunks.
    """
    collection = get_chroma_collection(collection_name)
    try:
        matching = collection.get(where={"machine": {"$eq": machine_name}})
        if matching and matching.get("ids"):
            ids_to_delete = matching["ids"]
            collection.delete(ids=ids_to_delete)
            invalidate_machines_cache()
            return len(ids_to_delete)
    except Exception as err:
        print(f"[delete_by_machine error]: {err}")
    invalidate_machines_cache()
    return 0

def get_distinct_machines(collection_name: str = "machine_manuals") -> List[str]:
    """
    Returns distinct machine names currently indexed in ChromaDB.
    Uses in-memory caching to avoid table scans on the query hot path.
    """
    global _CACHED_MACHINES
    if _CACHED_MACHINES is not None:
        return _CACHED_MACHINES

    collection = get_chroma_collection(collection_name)
    try:
        res = collection.get(include=["metadatas"])
        machines = set()
        if res and res.get("metadatas"):
            for m in res["metadatas"]:
                mach = m.get("machine")
                if mach and mach != "Unknown":
                    machines.add(mach)
        _CACHED_MACHINES = sorted(list(machines))
    except Exception:
        _CACHED_MACHINES = []
    return _CACHED_MACHINES

def get_manuals_summary(collection_name: str = "machine_manuals", manuals_dir: str = "data/manuals") -> List[Dict[str, Any]]:
    """
    Returns summary info for all indexed manuals: machine, filename, chunk_count, and updated_at.
    """
    collection = get_chroma_collection(collection_name)
    machine_counts: Dict[str, int] = {}
    machine_filenames: Dict[str, str] = {}

    try:
        res = collection.get(include=["metadatas"])
        if res and res.get("metadatas"):
            for m in res["metadatas"]:
                mach = m.get("machine")
                if not mach or mach == "Unknown":
                    continue
                machine_counts[mach] = machine_counts.get(mach, 0) + 1
                if mach not in machine_filenames and m.get("manual"):
                    machine_filenames[mach] = m["manual"]
    except Exception as err:
        print(f"[get_manuals_summary error]: {err}")

    # Map disk files to timestamps
    file_mtimes: Dict[str, str] = {}
    if os.path.exists(manuals_dir):
        for fname in os.listdir(manuals_dir):
            if fname.endswith(".txt"):
                fpath = os.path.join(manuals_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    file_mtimes[fname] = datetime.fromtimestamp(mtime).isoformat()
                except Exception:
                    pass

    summary = []
    for mach, count in sorted(machine_counts.items()):
        fname = machine_filenames.get(mach, f"{mach.lower().replace(' ', '_')}.txt")
        mtime_str = file_mtimes.get(fname, datetime.now().isoformat())
        summary.append({
            "machine": mach,
            "filename": fname,
            "chunk_count": count,
            "updated_at": mtime_str
        })

    return summary

def search(query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Performs similarity search in Chroma collection.
    Returns top k chunks with similarity scores.
    """
    collection = get_chroma_collection("machine_manuals")

    where_clause = None
    if filter_metadata:
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
            sim_score = max(0.0, 1.0 - dist)
            formatted_results.append({
                "text": doc,
                "machine": meta.get("machine"),
                "model": meta.get("model"),
                "manual": meta.get("manual"),
                "section": meta.get("section"),
                "page": meta.get("page"),
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
    reset_collection()
    chunks = load_and_chunk_manuals()
    indexed_count = index_chunks(chunks)
    print(f"Indexed {indexed_count} chunks into Chroma DB.")
    print("Distinct machines:", get_distinct_machines())
    print("Summary:", get_manuals_summary())
