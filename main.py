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

def write_guidelines_file():
    guidelines_text = """====================================================================
           交換機專案甘特圖自動化工具 - 表格排版規則與限制說明
====================================================================
此檔案由系統執行時自動更新，請隨程式碼一同提交至 GitHub 進行版控。

當前版本規則與支援格式如下：

1. ⚠️ 表格判定原則 (Table Matching Rules)
   - 表格的第一列 (Header) 必須包含「專案」或「Project」字眼。
   - 同時必須包含「Milestone」、「c0-c5」或「p0-p5」任一關鍵字，否則該表格會被直接跳過。

2. 🚀 專案名稱與類型提取
   - 專案名稱儲存格內容會依換行符切割，忽略純減號分隔線（如 ------）。
   - 切割後，若內容大於等於 2 行，第一行將被識別為「架構/類型」（例如 VR, NPDP），後續行將合併為「專案名稱」。
   - 若只有單行，則無架構/類型，該行文字即為專案名稱。

3. 🕒 里程碑計畫填寫格式 (雙軌支援)
   本工具支援以下兩種表格排版格式，可於同一個網頁混合使用：
   
   【格式 A】單列單里程碑模式 (傳統舊格式)
     - 每一列代表一個里程碑。
     - Milestone 欄位填寫代號 (如 P0~P5 或 C0~C5)。
     - 日期欄位填寫具體日期 (使用 Confluence /date 巨集或純文字日期)。
     
   【格式 B】單列整合里程碑列表模式 (新式簡約格式 - 推薦)
     - 一個專案只佔用一列。
     - 在「目前 milestone 計畫」儲存格內，直接列出所有里程碑。
     - 支援以下格式：
       - Confluence 任務清單 (Checkbox)：[x] C0: 2026/02/26
       - 無序列表 (Bullet List) 或純文字換行：每一行寫出代號與日期，如 "P1: 2026-03-19"
       - **日期區間處理**：如果該里程碑包含日期區間，如 "P1: 2026-03-19 - 2026-06-11"，系統會自動抓取最後一個日期 (即結束日期 2026-06-11) 做為目標完工日。

4. 📅 日期格式限制
   - 支援格式：YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD。
   - 必須是實體存在的日期 (如 2026-02-31 會被判定為無效日期並被忽略)。
====================================================================
"""
    try:
        import os
        with open("guidelines.txt", "w", encoding="utf-8") as f:
            f.write(guidelines_text)
        logger.info("Successfully updated guidelines.txt user guide.")
    except Exception as e:
        logger.error(f"Failed to write guidelines.txt: {e}")

def main():
    write_guidelines_file()
    
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
