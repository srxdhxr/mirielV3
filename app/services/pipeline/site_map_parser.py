"""
SiteMap Parser - Fetches and parses sitemaps from websites
"""
import logging
import time
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class SiteMapParser:
    """
    Parser to extract URLs from website sitemaps
    
    Usage:
        parser = SiteMapParser("https://example.com")
        urls = parser.get_urls()
    """
    
    def __init__(self, base_url: str):
        """
        Initialize the sitemap parser
        
        Args:
            base_url: The base URL of the website to parse (e.g., "https://example.com")
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        
        # Create a requests session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MirielBot/1.0; +http://miriel.ai/bot)'
        })
        
        logger.info(f"Initialized SiteMapParser for: {self.base_url}")
    
    def get_urls(self) -> List[str]:
        """
        Main method to get all URLs from sitemap
        
        Returns:
            List[str]: List of URLs found in the sitemap
        """
        return self.get_sitemap_urls()
    
    def get_sitemap_urls(self) -> List[str]:
        """Get URLs from sitemap"""

        # Ensure base_url doesn't end with slash for proper URL construction
        base = self.base_url
        
        # Try to find sitemap
        sitemap_urls = [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/sitemap.xml.gz"
        ]
        
        # Try robots.txt first
        try:
            robots_url = f"{base}/robots.txt"
            logger.info(f"Checking robots.txt: {robots_url}")
            time.sleep(1)  # Be respectful
            response = self.session.get(robots_url, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                logger.info("Successfully fetched robots.txt")
                for line in response.text.split('\n'):
                    try:
                        line_clean = str(line).strip()
                        # Check for sitemap with case-insensitive matching
                        if line_clean.lower().startswith('sitemap:'):
                            sitemap_url = line_clean.split(':', 1)[1].strip()
                            if sitemap_url:
                                logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
                                sitemap_urls.insert(0, sitemap_url)  # Prioritize robots.txt sitemap
                    except Exception as e:
                        logger.warning(f"Error parsing robots.txt line: {e}")
                        continue
            else:
                logger.warning(f"robots.txt returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt: {e}")
            
        # Try common sitemap URLs if not found in robots.txt
        logger.info(f"Trying sitemap URLs: {sitemap_urls}")
        for sitemap_url in sitemap_urls:
            try:
                logger.info(f"Fetching sitemap: {sitemap_url}")
                time.sleep(1)  # Be respectful between requests
                response = self.session.get(sitemap_url, timeout=15, allow_redirects=True)
                logger.info(f"Sitemap response status: {response.status_code}")
                if response.status_code == 200:
                    urls = self.parse_sitemap(response.content)
                    # Deduplicate URLs before returning
                    unique_urls = list(dict.fromkeys(urls))  # Preserves order
                    logger.info(f"Found {len(urls)} URLs ({len(unique_urls)} unique) in sitemap")
                    return unique_urls
            except Exception as e:
                logger.warning(f"Could not fetch sitemap {sitemap_url}: {e}")
                continue
                
        logger.warning(f"No sitemap found for {self.base_url}")
        return []

    def parse_sitemap(self, xml_content: bytes) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        urls = []
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            logger.info(f"Sitemap root tag: {root.tag}")
            
            # Check if it's a sitemap index
            if 'sitemapindex' in root.tag.lower():
                logger.info("Found sitemap index")
                # Find all sitemap entries
                for sitemap_elem in root.iter():
                    if 'sitemap' in sitemap_elem.tag.lower():
                        for child in sitemap_elem:
                            if 'loc' in child.tag.lower() and child.text:
                                logger.info(f"Processing sub-sitemap: {child.text}")
                                try:
                                    time.sleep(1)  # Be respectful
                                    sub_response = self.session.get(child.text, timeout=10)
                                    if sub_response.status_code == 200:
                                        sub_urls = self.parse_sitemap(sub_response.content)
                                        urls.extend(sub_urls)
                                        logger.info(f"Found {len(sub_urls)} URLs in sub-sitemap")
                                except Exception as e:
                                    logger.warning(f"Failed to fetch sub-sitemap {child.text}: {e}")
            else:
                # Handle regular sitemap - extract all URLs
                logger.info("Found regular sitemap, extracting URLs")
                url_count = 0
                
                # Iterate through all elements to find loc tags
                for elem in root.iter():
                    if 'loc' in elem.tag.lower() and elem.text:
                        url = elem.text.strip()
                        if self.is_valid_url(url):
                            urls.append(url)
                            url_count += 1
                            if url_count <= 5:  # Log first few URLs for debugging
                                logger.info(f"Found URL: {url}")
                
                logger.info(f"Extracted {url_count} valid URLs from regular sitemap")
                        
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")
            logger.error(f"XML content preview: {xml_content[:200]}...")
            
        return urls[0:10]
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and belongs to the same domain
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be same domain
            if parsed.netloc != self.domain:
                logger.debug(f"Skipping URL from different domain: {url}")
                return False
            
            # Skip common file extensions
            skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', 
                             '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                logger.debug(f"Skipping file URL: {url}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating URL {url}: {e}")
            return False


# # Example usage
# if __name__ == "__main__":
#     # Test the parser
#     parser = SiteMapParser("https://www.teachersfcu.org/")
#     urls = parser.get_urls()
#     print(f"Found {len(urls)} URLs:")
#     for url in urls:  # Print first 10
#         print(f"  - {url}")

