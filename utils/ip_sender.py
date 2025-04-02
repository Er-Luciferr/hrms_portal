import socket
import requests
import os
import logging
import time
import random

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ip_sender")

def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use an external IP to determine the outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        logger.info(f"Detected private IP: {ip}")
    except Exception as e:
        ip = "127.0.0.1"
        logger.warning(f"Error detecting private IP, using {ip}: {e}")
    finally:
        s.close()
    return ip

def send_private_ip_to_endpoint():
    """
    Send private IP to the configured endpoint.
    Implements retry logic with exponential backoff.
    """
    max_retries = 5
    retry_delay = 1  # Start with 1 second delay, will increase exponentially
    
    try:
        private_ip = get_private_ip()
        endpoint = os.environ.get("IP_REPORTING_ENDPOINT", "http://localhost:5000/api/ip-report")
        
        # In cloud environments, use the actual server hostname, not localhost
        if "localhost" in endpoint:
            # Check if we have a hostname in environment variables
            server_host = os.environ.get("SERVER_HOST", None)
            if server_host:
                endpoint = endpoint.replace("localhost", server_host)
                logger.info(f"Using server hostname: {server_host}")
        
        logger.info(f"Sending private IP {private_ip} to endpoint: {endpoint}")
        
        data = {"private_ip": private_ip}
        
        # Try to send with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt+1}/{max_retries} to send IP")
                response = requests.post(endpoint, json=data, timeout=10)
                
                # Check if the request was successful
                if response.status_code in (200, 201):
                    logger.info(f"Private IP ({private_ip}) sent successfully to {endpoint}")
                    return True
                else:
                    logger.warning(f"Failed to send IP: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt+1}: {e}")
            
            # If we get here, the attempt failed - wait before retrying
            if attempt < max_retries - 1:  # Don't sleep after the last attempt
                sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        
        logger.error(f"Failed to send IP after {max_retries} attempts")
        return False
    except Exception as e:
        logger.error(f"Error sending private IP: {e}")
        return False

if __name__ == "__main__":
    send_private_ip_to_endpoint() 