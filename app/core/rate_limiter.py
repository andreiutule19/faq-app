import time
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OpenAIRateLimiter:
    
    
    def __init__(self, 
                 rpm_limit: int = 45,          
                 rpd_limit: int = 1000,      
                 tpm_limit: int = 200000,     
                 tpd_limit: int = 1000000):    
        
    
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpm_limit = tpm_limit
        self.tpd_limit = tpd_limit
        
        self.requests_minute: List[float] = []
        self.requests_day: List[float] = []
        self.tokens_minute: List[tuple] = [] 
        self.tokens_day: List[tuple] = []     
        
        self._lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 100):

        async with self._lock:
            now = time.time()
            self._cleanup_old_entries(now)
        
            wait_time = self._calculate_wait_time(now, estimated_tokens)
            
            if wait_time > 0:
                logger.warning(f"Rate limit protection: waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
            
                now = time.time()
                self._cleanup_old_entries(now)
            
       
            self._record_request(now, estimated_tokens)
            status = self._get_current_status(now)
            logger.debug(f"Rate limiter status: {status}")

    def _cleanup_old_entries(self, now: float):
  
        minute_ago = now - 60
        day_ago = now - (24 * 60 * 60)
   
        self.requests_minute = [t for t in self.requests_minute if t > minute_ago]
        self.tokens_minute = [(t, tokens) for t, tokens in self.tokens_minute if t > minute_ago]
       
        self.requests_day = [t for t in self.requests_day if t > day_ago]
        self.tokens_day = [(t, tokens) for t, tokens in self.tokens_day if t > day_ago]

    def _calculate_wait_time(self, now: float, estimated_tokens: int) -> float:
      
        wait_times = []
     
        if len(self.requests_minute) >= self.rpm_limit:
            oldest_request = min(self.requests_minute)
            rpm_wait = 60 - (now - oldest_request) + 1
            wait_times.append(rpm_wait)
            logger.debug(f"RPM limit check: {len(self.requests_minute)}/{self.rpm_limit}, wait: {rpm_wait:.2f}s")
    
        if len(self.requests_day) >= self.rpd_limit:
            oldest_request = min(self.requests_day)
            rpd_wait = (24 * 60 * 60) - (now - oldest_request) + 1
            wait_times.append(rpd_wait)
            logger.debug(f"RPD limit check: {len(self.requests_day)}/{self.rpd_limit}, wait: {rpd_wait:.2f}s")
        
        
        current_tokens_minute = sum(tokens for _, tokens in self.tokens_minute)
        if current_tokens_minute + estimated_tokens > self.tpm_limit:
            if self.tokens_minute:
                oldest_token_request = min(t for t, _ in self.tokens_minute)
                tpm_wait = 60 - (now - oldest_token_request) + 1
                wait_times.append(tpm_wait)
                logger.debug(f"TPM limit check: {current_tokens_minute + estimated_tokens}/{self.tpm_limit}, wait: {tpm_wait:.2f}s")
        
     
        current_tokens_day = sum(tokens for _, tokens in self.tokens_day)
        if current_tokens_day + estimated_tokens > self.tpd_limit:
            if self.tokens_day:
                oldest_token_request = min(t for t, _ in self.tokens_day)
                tpd_wait = (24 * 60 * 60) - (now - oldest_token_request) + 1
                wait_times.append(tpd_wait)
                logger.debug(f"TPD limit check: {current_tokens_day + estimated_tokens}/{self.tpd_limit}, wait: {tpd_wait:.2f}s")
        
        return max(wait_times) if wait_times else 0

    def _record_request(self, now: float, tokens_used: int):
     
        self.requests_minute.append(now)
        self.requests_day.append(now)
        self.tokens_minute.append((now, tokens_used))
        self.tokens_day.append((now, tokens_used))

    def _get_current_status(self, now: float) -> Dict:
        
        current_tokens_minute = sum(tokens for _, tokens in self.tokens_minute)
        current_tokens_day = sum(tokens for _, tokens in self.tokens_day)
        
        return {
            "rpm": {
                "current": len(self.requests_minute),
                "limit": self.rpm_limit,
                "remaining": max(0, self.rpm_limit - len(self.requests_minute))
            },
            "rpd": {
                "current": len(self.requests_day),
                "limit": self.rpd_limit,
                "remaining": max(0, self.rpd_limit - len(self.requests_day))
            },
            "tpm": {
                "current": current_tokens_minute,
                "limit": self.tpm_limit,
                "remaining": max(0, self.tpm_limit - current_tokens_minute)
            },
            "tpd": {
                "current": current_tokens_day,
                "limit": self.tpd_limit,
                "remaining": max(0, self.tpd_limit - current_tokens_day)
            }
        }

    def get_status(self) -> Dict:
        
        now = time.time()
        self._cleanup_old_entries(now)
        return self._get_current_status(now)

    def update_limits(self, rpm: int = None, rpd: int = None, tpm: int = None, tpd: int = None):
     
        if rpm is not None:
            self.rpm_limit = rpm
            logger.info(f"Updated RPM limit to {rpm}")
        if rpd is not None:
            self.rpd_limit = rpd
            logger.info(f"Updated RPD limit to {rpd}")
        if tpm is not None:
            self.tpm_limit = tpm
            logger.info(f"Updated TPM limit to {tpm}")
        if tpd is not None:
            self.tpd_limit = tpd
            logger.info(f"Updated TPD limit to {tpd}")



openai_rate_limiter = OpenAIRateLimiter(
    rpm_limit=45,        
    rpd_limit=1000,    
    tpm_limit=200000,    
    tpd_limit=1000000   
)