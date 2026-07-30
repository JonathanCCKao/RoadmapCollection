import argparse
import sys
import logging
from config import Config
from confluence_client import ConfluenceClient
from parser import parse_confluence_table
from generator import generate_chart
from updater import update_html_body

# Configure logs to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Confluence C0-C5 Roadmap Gantt Chart Automation Tool")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Fetch and parse page, generate Gantt syntax, but do not write back to Confluence."
    )
    args = parser.parse_args()

    # 1. Load and validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set the required environment variables (e.g., CONFLUENCE_URL, CONFLUENCE_TOKEN).")
        sys.exit(1)

    # 2. Initialize Confluence Client
    client = ConfluenceClient(
        base_url=Config.URL,
        auth_type=Config.AUTH_TYPE,
        token=Config.TOKEN,
        username=Config.USER
    )

    # 3. Fetch source page content
    try:
        source_page = client.get_page(Config.SOURCE_PAGE_ID)
    except Exception as e:
        logger.error(f"Failed to fetch source page {Config.SOURCE_PAGE_ID}: {e}")
        sys.exit(1)

    title = source_page.get("title", "")
    version_num = source_page.get("version", {}).get("number", 1)
    body_html = source_page.get("body", {}).get("storage", {}).get("value", "")

    if not body_html:
        logger.error("Source page has no body content or storage format is empty.")
        sys.exit(1)

    # 4. Parse projects from HTML
    logger.info("Parsing source page content for project milestones table...")
    projects = parse_confluence_table(body_html)
    if not projects:
        logger.warning("No projects were parsed from the page. Gantt chart will be empty.")
        sys.exit(0)

    # 5. Generate Gantt Chart
    chart_code = generate_chart(
        projects, 
        mode=Config.RENDER_MODE, 
        scale=Config.TIMELINE_SCALE, 
        zoom=Config.ZOOM_FACTOR
    )
    logger.info(f"Generated {Config.RENDER_MODE.upper()} Gantt Chart:\n{chart_code}")

    if args.dry_run:
        logger.info("Dry-run mode active. Skipping page update in Confluence.")
        sys.exit(0)

    # 6. Fetch target page metadata (if target page is different from source page)
    if Config.TARGET_PAGE_ID != Config.SOURCE_PAGE_ID:
        try:
            target_page = client.get_page(Config.TARGET_PAGE_ID)
            target_title = target_page.get("title", "")
            target_version_num = target_page.get("version", {}).get("number", 1)
            target_body_html = target_page.get("body", {}).get("storage", {}).get("value", "")
        except Exception as e:
            logger.error(f"Failed to fetch target page {Config.TARGET_PAGE_ID}: {e}")
            sys.exit(1)
    else:
        target_title = title
        target_version_num = version_num
        target_body_html = body_html

    # 7. Update target page body
    updated_body = update_html_body(
        target_body_html, 
        chart_code, 
        mode=Config.RENDER_MODE, 
        insert_position=Config.INSERT_POSITION
    )

    # 8. Push update back to Confluence
    try:
        client.update_page(Config.TARGET_PAGE_ID, target_title, updated_body, target_version_num)
        logger.info(f"Successfully updated Confluence page {Config.TARGET_PAGE_ID}!")
    except Exception as e:
        logger.error(f"Failed to update page {Config.TARGET_PAGE_ID}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
