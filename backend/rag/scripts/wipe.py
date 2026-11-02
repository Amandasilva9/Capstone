#Helper script to delete the stored embedings in order to re-embed edited chunks
import chromadb
chromadb.PersistentClient(path="backend/rag/./chroma_db").delete_collection("papers")