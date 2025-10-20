"""
Web Scraper - Scrapes individual URLs and extracts clean content
"""
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import trafilatura
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class Scraper:
    """
    Web scraper that uses Playwright for JS rendering and trafilatura for content extraction
    
    Usage:
        scraper = Scraper(tenant_id=1, output_dir="scraped_data")
        result = scraper.scrape("https://example.com/page")
    """
    
    def __init__(self, tenant_id: int, output_dir: str = "scraped_data"):
        """
        Initialize the scraper
        
        Args:
            tenant_id: Tenant ID for organizing scraped data
            output_dir: Base directory for storing scraped content
        """
        self.tenant_id = tenant_id
        self.output_dir = output_dir
        self._ensure_output_dir()
        
        logger.info(f"Initialized Scraper for tenant {tenant_id}")
    
    def _ensure_output_dir(self):
        """Create base output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def _get_tenant_date_dir(self) -> str:
        """
        Get the tenant-specific directory path with today's date
        
        Returns:
            str: Path like "scraped_data/1/2025-01-15"
        """
        today = datetime.now().strftime("%Y-%m-%d")
        tenant_dir = os.path.join(self.output_dir, str(self.tenant_id), today)
        
        if not os.path.exists(tenant_dir):
            os.makedirs(tenant_dir, exist_ok=True)
            logger.debug(f"Created tenant date directory: {tenant_dir}")
        
        return tenant_dir
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate a safe filename from URL
        
        Args:
            url: The URL to convert to filename
            
        Returns:
            str: Safe filename like "about_company.json"
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if path_parts and path_parts[0]:
            # Join path parts with underscore
            filename = '_'.join(part for part in path_parts if part)
        else:
            # Root URL - use domain or "index"
            filename = 'index'
        
        # Clean filename - only alphanumeric, underscore, hyphen
        filename = re.sub(r'[^\w\-]', '_', filename)
        
        # Limit length to avoid filesystem issues
        if len(filename) > 200:
            filename = filename[:200]
        
        return f"{filename}.json"
    
    def _fetch_html(self, url: str, timeout: int = 30000) -> Optional[str]:
        """
        Fetch HTML content using Playwright (handles JavaScript)
        
        Args:
            url: URL to fetch
            timeout: Timeout in milliseconds (default 30 seconds)
            
        Returns:
            str: HTML content or None if failed
        """
        try:
            logger.info(f"Fetching URL with Playwright: {url}")
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate to URL
                response = page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                
                if not response or response.status >= 400:
                    logger.error(f"Failed to load URL: HTTP {response.status if response else 'No response'}")
                    browser.close()
                    return None
                
                # Wait a bit for dynamic content to load
                page.wait_for_timeout(1000)
                
                # Get full HTML after JS rendering
                html = page.content()
                browser.close()
                
                logger.info(f"Successfully fetched {len(html)} bytes from {url}")
                return html
                
        except PlaywrightTimeout:
            logger.error(f"Timeout fetching URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None
    
    def _extract_content(self, html: str) -> Optional[str]:
        """
        Extract clean text content using trafilatura
        
        Args:
            html: Raw HTML content
            
        Returns:
            str: Clean extracted text or None if failed
        """
        try:
            # Extract main content using trafilatura
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            if content:
                logger.info(f"Extracted {len(content)} characters of clean content")
                return content
            else:
                logger.warning("No content extracted by trafilatura")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return None
    
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrape a URL and save to JSON file
        
        Args:
            url: URL to scrape
            
        Returns:
            str: Path to saved JSON file, or None if scraping failed
        """
        logger.info(f"🕷️  Starting scrape for: {url}")
        
        try:
            # Step 1: Fetch HTML with Playwright
            html = self._fetch_html(url)
            if not html:
                logger.error(f"Failed to fetch HTML for {url}")
                return None
            
            # Step 2: Extract clean content with trafilatura
            content = self._extract_content(html)
            if not content:
                logger.error(f"Failed to extract content from {url}")
                return None
            
            # Step 3: Calculate word count
            word_count = len(content.split())
            logger.info(f"Content has {word_count} words")
            
            # Step 4: Prepare data
            scraped_data = {
                "url": url,
                "content": content,
                "word_count": word_count,
                "scraped_date": datetime.now().isoformat()
            }
            
            # Step 5: Generate file path
            tenant_date_dir = self._get_tenant_date_dir()
            filename = self._generate_filename(url)
            file_path = os.path.join(tenant_date_dir, filename)
            
            # Handle duplicate filenames
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Step 6: Save to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Successfully scraped and saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            return None
    
    def scrape_multiple(self, urls: list) -> dict:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            dict: Summary with success/failure counts and file paths
        """
        logger.info(f"Starting batch scrape of {len(urls)} URLs")
        
        results = {
            "total": len(urls),
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Scraping: {url}")
            
            file_path = self.scrape(url)
            if file_path:
                results["success"] += 1
                results["files"].append(file_path)
            else:
                results["failed"] += 1
        
        logger.info(f"Batch scrape complete: {results['success']} success, {results['failed']} failed")
        return results


# Example usage
# if __name__ == "__main__":
#     # Test the scraper
#     scraper = Scraper(tenant_id=1, output_dir="scraped_data")
    
#     # Scrape a single URL
#     result = scraper.scrape("https://www.teachersfcu.org/")
    
#     if result:
#         print(f"✅ Scraped successfully: {result}")
#     else:
#         print("❌ Scraping failed")

