import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from scraper import playwright_scraper

class TestScraperResilience(unittest.IsolatedAsyncioTestCase):
    
    async def test_async_retry_success(self):
        """Verify that async_retry eventually succeeds."""
        mock_func = AsyncMock()
        mock_func.side_effect = [ValueError("Fail 1"), ValueError("Fail 2"), "Success"]
        
        @playwright_scraper.async_retry(retries=3, delay=0.1)
        async def decorated_func():
            return await mock_func()
            
        result = await decorated_func()
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 3)

    async def test_async_retry_failure(self):
        """Verify that async_retry fails after max retries."""
        mock_func = AsyncMock()
        mock_func.side_effect = ValueError("Always Fail")
        
        @playwright_scraper.async_retry(retries=2, delay=0.1)
        async def decorated_func():
            await mock_func()
            
        with self.assertRaises(ValueError):
            await decorated_func()
        self.assertEqual(mock_func.call_count, 2)

    async def test_resilient_locator_fallback(self):
        """Verify that get_resilient_locator tries multiple selectors."""
        page = MagicMock()
        
        mock_locator_fail = MagicMock()
        mock_locator_fail.count = AsyncMock(return_value=0)
        
        mock_locator_success = MagicMock()
        mock_locator_success.count = AsyncMock(return_value=1)
        
        # side_effect returns failure for first selector, success for second
        page.locator.side_effect = [mock_locator_fail, mock_locator_success]
        
        selectors = [".wrong-class", ".correct-class"]
        result = await playwright_scraper.get_resilient_locator(page, selectors)
        
        self.assertEqual(result, mock_locator_success)
        self.assertEqual(page.locator.call_count, 2)

if __name__ == "__main__":
    unittest.main()
