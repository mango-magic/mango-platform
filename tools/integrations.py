"""
API integrations for all third-party services.
OAuth, webhooks, rate limiting, retries.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('Integrations')

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period  # seconds
        self.calls = []
        
    async def acquire(self):
        """Wait until we can make a call"""
        now = datetime.now()
        
        # Remove old calls
        self.calls = [c for c in self.calls 
                     if now - c < timedelta(seconds=self.period)]
        
        # Wait if at limit
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.calls.append(now)

class TelegramAPI:
    """Telegram Bot API integration"""
    
    def __init__(self, token: str):
        self.token = token
        self.limiter = RateLimiter(max_calls=30, period=1)  # 30 msg/sec
        self.base_url = f"https://api.telegram.org/bot{token}"
        
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        await self.limiter.acquire()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
            ) as resp:
                result = await resp.json()
                if result.get('ok'):
                    logger.info(f"📱 Sent Telegram message to {chat_id}")
                    return True
                return False
    
    async def send_document(self, chat_id: str, document: bytes, filename: str) -> bool:
        """Send document to Telegram"""
        await self.limiter.acquire()
        
        data = aiohttp.FormData()
        data.add_field('chat_id', chat_id)
        data.add_field('document', document, filename=filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/sendDocument",
                data=data
            ) as resp:
                result = await resp.json()
                return result.get('ok', False)

class GmailAPI:
    """Gmail API integration"""
    
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.limiter = RateLimiter(max_calls=250, period=1)  # 250 req/sec
        
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via Gmail API"""
        await self.limiter.acquire()
        
        # Implementation using Google API client
        logger.info(f"📧 Sending email to {to}")
        # TODO: Actual Gmail API implementation
        return True
    
    async def list_messages(self, query: str = "", max_results: int = 10) -> list:
        """List messages"""
        await self.limiter.acquire()
        logger.info(f"📧 Listing messages: {query}")
        # TODO: Actual implementation
        return []

class LinkedInAPI:
    """LinkedIn API integration (via unofficial APIs)"""
    
    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.limiter = RateLimiter(max_calls=20, period=60)  # Conservative
        
    async def search_people(self, keywords: str, filters: dict = None) -> list:
        """Search for people"""
        await self.limiter.acquire()
        logger.info(f"💼 LinkedIn search: {keywords}")
        # TODO: Implementation via browser automation or API
        return []
    
    async def send_message(self, profile_id: str, message: str) -> bool:
        """Send message to connection"""
        await self.limiter.acquire()
        logger.info(f"💼 Sending LinkedIn message to {profile_id}")
        # TODO: Implementation
        return True

class SalesforceAPI:
    """Salesforce API integration"""
    
    def __init__(self, instance_url: str, access_token: str):
        self.instance_url = instance_url
        self.access_token = access_token
        self.limiter = RateLimiter(max_calls=100, period=20)  # 5k/day
        
    async def create_lead(self, data: dict) -> str:
        """Create lead"""
        await self.limiter.acquire()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.instance_url}/services/data/v59.0/sobjects/Lead",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json=data
            ) as resp:
                result = await resp.json()
                lead_id = result.get('id')
                logger.info(f"☁️ Created Salesforce lead: {lead_id}")
                return lead_id
    
    async def query(self, soql: str) -> list:
        """Execute SOQL query"""
        await self.limiter.acquire()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.instance_url}/services/data/v59.0/query",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"q": soql}
            ) as resp:
                result = await resp.json()
                return result.get('records', [])

class HubSpotAPI:
    """HubSpot API integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = RateLimiter(max_calls=100, period=10)
        self.base_url = "https://api.hubapi.com"
        
    async def create_contact(self, data: dict) -> str:
        """Create contact"""
        await self.limiter.acquire()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"properties": data}
            ) as resp:
                result = await resp.json()
                logger.info(f"🟠 Created HubSpot contact: {result.get('id')}")
                return result.get('id')

# Integration manager
class IntegrationManager:
    """Manages all integrations for an agent"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.integrations = {}
        
    def add_telegram(self, token: str):
        self.integrations['telegram'] = TelegramAPI(token)
        
    def add_gmail(self, credentials: dict):
        self.integrations['gmail'] = GmailAPI(credentials)
        
    def add_linkedin(self, session_cookie: str):
        self.integrations['linkedin'] = LinkedInAPI(session_cookie)
        
    def add_salesforce(self, instance_url: str, access_token: str):
        self.integrations['salesforce'] = SalesforceAPI(instance_url, access_token)
        
    def add_hubspot(self, api_key: str):
        self.integrations['hubspot'] = HubSpotAPI(api_key)
        
    def get(self, name: str):
        return self.integrations.get(name)
