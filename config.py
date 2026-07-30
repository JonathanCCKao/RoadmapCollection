import os

def load_dotenv():
    """Loads environment variables from a local .env or DC_Key.env.txt file if it exists."""
    for filename in [".env", "DC_Key.env.txt"]:
        env_path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        # Strip spaces and optional quotes
                        os.environ[key.strip()] = val.strip().strip("'\"")
            break

# Load variables from .env file before initializing Config properties
load_dotenv()

class Config:
    # Confluence API settings
    URL = os.getenv("CONFLUENCE_URL", "https://wiki.moxa.com").rstrip("/")
    USER = os.getenv("CONFLUENCE_USER", "")
    TOKEN = os.getenv("CONFLUENCE_TOKEN", "")
    
    # Auth type: 'basic' or 'bearer'
    # If USER is provided, defaults to basic auth (USER + TOKEN).
    # If USER is not provided but TOKEN is, defaults to bearer token auth.
    AUTH_TYPE = os.getenv("CONFLUENCE_AUTH_TYPE", "basic" if USER else "bearer")
    
    # Page configuration
    SOURCE_PAGE_ID = os.getenv("SOURCE_PAGE_ID", "627857514")
    TARGET_PAGE_ID = os.getenv("TARGET_PAGE_ID", SOURCE_PAGE_ID)
    
    # Position to insert the chart (if no existing block is found): 'top' or 'bottom'
    INSERT_POSITION = os.getenv("INSERT_POSITION", "top").lower()

    # Render mode: 'mermaid' or 'plantuml'
    RENDER_MODE = os.getenv("RENDER_MODE", "plantuml").lower()

    # Zoom factor for PlantUML Gantt charts
    ZOOM_FACTOR = int(os.getenv("ZOOM_FACTOR", "5"))

    # Timeline scale: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    TIMELINE_SCALE = os.getenv("TIMELINE_SCALE", "quarterly").lower()

    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if not cls.URL:
            raise ValueError("CONFLUENCE_URL is required.")
        if not cls.TOKEN:
            raise ValueError("CONFLUENCE_TOKEN is required.")
        if cls.AUTH_TYPE == "basic" and not cls.USER:
            raise ValueError("CONFLUENCE_USER is required for Basic authentication.")
        if cls.INSERT_POSITION not in ("top", "bottom"):
            raise ValueError("INSERT_POSITION must be either 'top' or 'bottom'.")
        if cls.RENDER_MODE not in ("mermaid", "plantuml"):
            raise ValueError("RENDER_MODE must be either 'mermaid' or 'plantuml'.")
        if cls.ZOOM_FACTOR <= 0:
            raise ValueError("ZOOM_FACTOR must be a positive integer.")
        if cls.TIMELINE_SCALE not in ("daily", "weekly", "monthly", "quarterly", "yearly"):
            raise ValueError("TIMELINE_SCALE must be one of 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'.")
