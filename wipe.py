#simple script to delete the stored embedings in order to re-embed edited chunks
import chromadb
chromadb.PersistentClient(path="./chroma_db").delete_collection("papers")