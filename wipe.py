import chromadb
chromadb.PersistentClient(path="./chroma_db").delete_collection("papers")