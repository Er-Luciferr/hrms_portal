import requests
from utils.ip_utils import get_private_ip
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_private_ip_to_endpoint():
    """
    Sends the private IP address to a configured endpoint.
    Returns True if successful, False otherwise.
    """
    try:
        # Get the private IP address
        private_ip = get_private_ip()
        
        # Get the endpoint URL from environment variable or use default
        endpoint = os.environ.get(
            "IP_REPORTING_ENDPOINT", 
            "http://localhost:8501/api/ip-report"
        )
        
        # Prepare the data payload
        data = {"private_ip": private_ip}
        
        # Send the data to the endpoint
        response = requests.post(endpoint, json=data, timeout=5)
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"Private IP ({private_ip}) sent successfully to {endpoint}")
            return True
        else:
            logger.warning(f"Failed to send IP: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending private IP to endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    # If run directly, send the IP and print the result
    private_ip = get_private_ip()
    print(f"Private IP: {private_ip}")
    
    result = send_private_ip_to_endpoint()
    if result:
        print("Successfully sent IP to endpoint")
    else:
        print("Failed to send IP to endpoint") 