import logging
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class Chunker:
    """
    Chunks scraped content using LangChain text splitter
    """
    
    def __init__(self, tenant_id: int, user_id: int, output_dir: str = "chunked_data"):
        """
        Initialize Chunker
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            output_dir: Base directory for chunked files
        """
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.output_dir = output_dir
        self.tenant_output_dir = os.path.join(output_dir, str(tenant_id))
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len
        )
        
        # Ensure output directory exists
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.tenant_output_dir, exist_ok=True)
        logger.info(f"Chunker output directory: {self.tenant_output_dir}")
    
    def chunk(self, file_path: str, url: str) -> Optional[str]:
        """
        Chunk a scraped file
        
        Args:
            file_path: Path to scraped JSON file
            url: URL of the content
            
        Returns:
            Path to chunked file, or None if failed
        """
        try:
            logger.info(f"📄 Chunking file: {file_path}")
            
            # Step 1: Read scraped JSON file
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            # Step 2: Extract content
            content = scraped_data.get('content', '')
            if not content:
                logger.warning(f"No content to chunk for {url}")
                return None
            
            # Step 3: Split text into chunks
            text_chunks = self.text_splitter.split_text(content)
            logger.info(f"Split into {len(text_chunks)} chunks")
            
            # Step 4: Build chunk data with metadata
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_data = {
                    "chunk": chunk_text,
                    "word_count": len(chunk_text.split()),
                    "chunked_at": datetime.utcnow().isoformat()
                }
                chunks.append(chunk_data)
            
            # Step 5: Prepare output data
            output_data = {
                "url": url,
                "chunks": chunks
            }
            
            # Step 6: Generate output filename (same name as input)
            filename = os.path.basename(file_path)
            output_path = os.path.join(self.tenant_output_dir, filename)
            
            # Step 7: Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Successfully chunked and saved to: {output_path}")
            logger.info(f"   Total chunks: {len(chunks)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error chunking {file_path}: {e}")
            return None
    
    def chunk_multiple(self, file_paths: list, urls: list) -> Dict[str, Any]:
        """
        Chunk multiple files
        
        Args:
            file_paths: List of file paths to chunk
            urls: Corresponding list of URLs
            
        Returns:
            Summary dict with success/failure counts
        """
        logger.info(f"Starting batch chunking of {len(file_paths)} files")
        
        results = {
            "total": len(file_paths),
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        for file_path, url in zip(file_paths, urls):
            output_path = self.chunk(file_path, url)
            if output_path:
                results["success"] += 1
                results["files"].append(output_path)
            else:
                results["failed"] += 1
        
        logger.info(f"✅ Batch chunking complete: {results['success']} success, {results['failed']} failed")
        return results


if __name__ == "__main__":
    # Example usage
    chunker = Chunker(tenant_id=1, user_id=1)
    
    # Chunk a single file
    output_path = chunker.chunk(
        file_path="scraped_data/2/2025-10-19/about_become-member.json",
        url="test.com"
    )
    
    if output_path:
        print(f"Chunked file saved to: {output_path}")

