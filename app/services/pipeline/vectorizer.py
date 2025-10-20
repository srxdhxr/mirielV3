import logging
import os
import json
from typing import Optional, Dict, Any, List
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Vectorizer:
    """
    Vectorizes chunked content and stores in ChromaDB
    Uses sentence-transformers for free local embeddings
    """
    
    def __init__(self, tenant_id: int, user_id: int, chroma_dir: str = "chroma_data"):
        """
        Initialize Vectorizer
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            chroma_dir: Base directory for ChromaDB storage
        """
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.chroma_dir = chroma_dir
        self.collection_name = f"tenant_{tenant_id}"
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model (free, local)
        logger.info("Loading sentence-transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded")
        
        # Get or create collection for this tenant
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection for tenant"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"tenant_id": self.tenant_id}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    def vectorize(self, chunked_file_path: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Vectorize a chunked file and store in ChromaDB
        
        Args:
            chunked_file_path: Path to chunked JSON file
            url: URL of the content
            
        Returns:
            Result dict with success status and count, or None if failed
        """
        try:
            logger.info(f"🔢 Vectorizing file: {chunked_file_path}")
            
            # Step 1: Read chunked JSON file
            if not os.path.exists(chunked_file_path):
                logger.error(f"File not found: {chunked_file_path}")
                return None
            
            with open(chunked_file_path, 'r', encoding='utf-8') as f:
                chunked_data = json.load(f)
            
            # Step 2: Extract chunks
            url_from_file = chunked_data.get('url', url)
            chunks = chunked_data.get('chunks', [])
            
            if not chunks:
                logger.warning(f"No chunks to vectorize for {url}")
                return None
            
            logger.info(f"Processing {len(chunks)} chunks...")
            
            # Step 3: Prepare data for batch insertion
            texts = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_text = chunk.get('chunk', '')
                if not chunk_text:
                    continue
                
                # Generate unique ID for this chunk
                chunk_id = f"{self.tenant_id}_{hash(url_from_file)}_{i}"
                
                # Prepare metadata
                metadata = {
                    "tenant_id": self.tenant_id,
                    "url": url_from_file,
                    "word_count": chunk.get('word_count', 0),
                    "chunk_index": i,
                    "chunked_at": chunk.get('chunked_at', ''),
                    "source_file": os.path.basename(chunked_file_path)
                }
                
                texts.append(chunk_text)
                metadatas.append(metadata)
                ids.append(chunk_id)
            
            if not texts:
                logger.warning(f"No valid chunks to vectorize for {url}")
                return None
            
            # Step 4: Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # Step 5: Insert into ChromaDB
            logger.info(f"Inserting {len(texts)} vectors into ChromaDB...")
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Successfully vectorized {len(texts)} chunks from {url}")
            
            return {
                "status": "success",
                "chunks_vectorized": len(texts),
                "url": url_from_file,
                "collection": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error vectorizing {chunked_file_path}: {e}")
            return None
    
    def search(self, query: str, n_results: int = 5, filter_url: Optional[str] = None) -> List[Dict]:
        """
        Search the vector database
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_url: Optional URL filter
            
        Returns:
            List of results with documents and metadata
        """
        try:
            where_filter = None
            if filter_url:
                where_filter = {"url": filter_url}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "tenant_id": self.tenant_id,
                "total_vectors": count
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    vectorizer = Vectorizer(tenant_id=2, user_id=1)
    
   
    # Test search
    search_results = vectorizer.search("Routing Number", n_results=3)
    print(f"🔍 Search results: {len(search_results)} found")
    for i, result in enumerate(search_results):
        print(f"\n{i+1}. {result['text'][:100]}...")
        print(f"   URL: {result['metadata']['url']}")

