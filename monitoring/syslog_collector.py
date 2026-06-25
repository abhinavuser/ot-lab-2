#!/usr/bin/env python3
"""
Syslog Collector for Railroad North
Receives syslog messages from all components
"""

import asyncio
import logging
import os
import socket
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SyslogCollector:
    def __init__(self, port=514, listen_ip='0.0.0.0'):
        self.port = port
        self.listen_ip = listen_ip
        self.message_count = 0
        self.last_sources = {}
        logger.info(f"Syslog Collector starting on {listen_ip}:{port}")
    
    async def handle_syslog(self, data, addr):
        self.message_count += 1
        source_ip = addr[0]
        self.last_sources[source_ip] = datetime.now().isoformat()
        
        try:
            message = data.decode('utf-8').strip()
            logger.info(f"[{source_ip}] {message}")
            
            if 'DEVICE_CONTROL' in message:
                logger.warning(f"[DEVICE_CONTROL] {message}")
            if 'EMERGENCY' in message or 'CRITICAL' in message:
                logger.error(f"[ALERT] {message}")
            if 'REJECTED' in message:
                logger.warning(f"[REJECTED] {message}")
        except Exception as e:
            logger.error(f"Error parsing syslog: {e}")
    
    async def start_server(self):
        logger.info("Starting UDP syslog server")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.listen_ip, self.port))
        sock.setblocking(False)
        
        loop = asyncio.get_event_loop()
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                await self.handle_syslog(data, addr)
            except BlockingIOError:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Server error: {e}")
                await asyncio.sleep(1)
    
    async def stats_reporter(self):
        while True:
            await asyncio.sleep(30)
            logger.info(f"Stats: {self.message_count} messages, {len(self.last_sources)} sources")
    
    async def run(self):
        await asyncio.gather(
            self.start_server(),
            self.stats_reporter()
        )


if __name__ == '__main__':
    collector = SyslogCollector(
        port=int(os.environ.get('SYSLOG_PORT', 514)),
        listen_ip=os.environ.get('LISTEN_IP', '0.0.0.0')
    )
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        logger.info("Syslog Collector stopped")
