"""
Browser automation for all agents using Playwright.
Each agent can control a real Chrome browser to do web tasks.
"""

import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import logging

logger = logging.getLogger('Browser')

class MangoBrowser:
    """Browser automation wrapper for agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def start(self):
        """Start browser instance"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        logger.info(f"🌐 Browser started for {self.agent_id}")
        
    async def stop(self):
        """Stop browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"🌐 Browser stopped for {self.agent_id}")
    
    async def goto(self, url: str):
        """Navigate to URL"""
        if not self.page:
            await self.start()
        await self.page.goto(url, wait_until='networkidle')
        logger.info(f"🌐 {self.agent_id} navigated to {url}")
        
    async def click(self, selector: str):
        """Click element"""
        await self.page.click(selector)
        logger.info(f"🌐 {self.agent_id} clicked {selector}")
    
    async def type(self, selector: str, text: str):
        """Type text"""
        await self.page.fill(selector, text)
        logger.info(f"🌐 {self.agent_id} typed into {selector}")
    
    async def screenshot(self, path: str):
        """Take screenshot"""
        await self.page.screenshot(path=path)
        logger.info(f"🌐 {self.agent_id} screenshot saved to {path}")
    
    async def get_text(self, selector: str) -> str:
        """Get text from element"""
        return await self.page.text_content(selector)
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000):
        """Wait for element"""
        await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def evaluate(self, script: str):
        """Execute JavaScript"""
        return await self.page.evaluate(script)
    
    # Gmail automation
    async def gmail_login(self, email: str, password: str):
        """Login to Gmail"""
        await self.goto('https://mail.google.com')
        await self.type('input[type="email"]', email)
        await self.click('button:has-text("Next")')
        await asyncio.sleep(2)
        await self.type('input[type="password"]', password)
        await self.click('button:has-text("Next")')
        await asyncio.sleep(3)
        logger.info(f"📧 Logged into Gmail as {email}")
    
    async def gmail_send_email(self, to: str, subject: str, body: str):
        """Send email via Gmail UI"""
        await self.click('div[role="button"]:has-text("Compose")')
        await asyncio.sleep(1)
        await self.type('input[name="to"]', to)
        await self.type('input[name="subjectbox"]', subject)
        await self.type('div[aria-label="Message Body"]', body)
        await self.click('div[role="button"]:has-text("Send")')
        logger.info(f"📧 Sent email to {to}")
    
    # LinkedIn automation
    async def linkedin_login(self, email: str, password: str):
        """Login to LinkedIn"""
        await self.goto('https://www.linkedin.com/login')
        await self.type('#username', email)
        await self.type('#password', password)
        await self.click('button[type="submit"]')
        await asyncio.sleep(3)
        logger.info(f"💼 Logged into LinkedIn as {email}")
    
    async def linkedin_send_connection_request(self, profile_url: str, message: str):
        """Send LinkedIn connection request"""
        await self.goto(profile_url)
        await asyncio.sleep(2)
        
        # Click Connect
        await self.click('button:has-text("Connect")')
        await asyncio.sleep(1)
        
        # Add note
        await self.click('button:has-text("Add a note")')
        await self.type('textarea', message)
        await self.click('button:has-text("Send")')
        logger.info(f"💼 Sent connection request to {profile_url}")
    
    # Salesforce automation
    async def salesforce_login(self, username: str, password: str):
        """Login to Salesforce"""
        await self.goto('https://login.salesforce.com')
        await self.type('#username', username)
        await self.type('#password', password)
        await self.click('#Login')
        await asyncio.sleep(3)
        logger.info(f"☁️ Logged into Salesforce as {username}")
    
    async def salesforce_create_lead(self, data: dict):
        """Create lead in Salesforce"""
        # Navigate to Leads
        await self.goto('https://your-instance.lightning.force.com/lightning/o/Lead/home')
        await asyncio.sleep(2)
        
        # Click New
        await self.click('button:has-text("New")')
        await asyncio.sleep(1)
        
        # Fill form
        for field, value in data.items():
            await self.type(f'input[name="{field}"]', value)
        
        # Save
        await self.click('button:has-text("Save")')
        logger.info(f"☁️ Created lead: {data.get('name', 'Unknown')}")
    
    # Generic form filling
    async def fill_form(self, form_data: dict):
        """Fill any form with provided data"""
        for selector, value in form_data.items():
            try:
                await self.type(selector, value)
            except Exception as e:
                logger.warning(f"Could not fill {selector}: {e}")
    
    async def submit_form(self, submit_selector: str):
        """Submit form"""
        await self.click(submit_selector)
        await asyncio.sleep(2)

# Global browser pool
_browser_pool = {}

async def get_browser(agent_id: str) -> MangoBrowser:
    """Get or create browser for agent"""
    if agent_id not in _browser_pool:
        browser = MangoBrowser(agent_id)
        await browser.start()
        _browser_pool[agent_id] = browser
    return _browser_pool[agent_id]

async def close_all_browsers():
    """Cleanup all browsers"""
    for browser in _browser_pool.values():
        await browser.stop()
    _browser_pool.clear()
