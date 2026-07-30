import requests
from requests.auth import HTTPBasicAuth
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ConfluenceClient:
    def __init__(self, base_url, auth_type, token, username=None):
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.token = token
        self.username = username
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Configure authentication
        if self.auth_type == "bearer":
            self.headers["Authorization"] = f"Bearer {self.token}"
            self.auth = None
        elif self.auth_type == "basic":
            self.auth = HTTPBasicAuth(self.username, self.token)
        else:
            self.auth = None
            logger.warning("No authentication method configured. Requests may fail.")

    def get_page(self, page_id):
        """
        Fetches the Confluence page metadata, title, version, and body storage.
        """
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,version,title"
        }
        logger.info(f"Fetching page {page_id} from {url}")
        
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def update_page(self, page_id, title, new_body, current_version):
        """
        Updates the Confluence page content. The version number must be incremented.
        """
        url = f"{self.base_url}/rest/api/content/{page_id}"
        next_version = current_version + 1
        
        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {
                "number": next_version
            },
            "body": {
                "storage": {
                    "value": new_body,
                    "representation": "storage"
                }
            }
        }
        
        logger.info(f"Updating page {page_id} to version {next_version}")
        response = requests.put(url, headers=self.headers, auth=self.auth, json=payload)
        response.raise_for_status()
        return response.json()
