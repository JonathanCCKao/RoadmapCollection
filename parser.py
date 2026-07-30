import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

# Regular expression to extract date in YYYY-MM-DD, YYYY/MM/DD or YYYY.MM.DD formats
DATE_RE = re.compile(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})")

def normalize_date(text):
    """
    Extracts and normalizes a date string to YYYY-MM-DD.
    Returns None if no valid date is found.
    """
    if not text:
        return None
    
    text = text.strip()
    match = DATE_RE.search(text)
    if match:
        year, month, day = match.groups()
        try:
            # Validate and format date
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError as e:
            logger.warning(f"Invalid date values parsed from '{text}': {e}")
            return None
    return None

def create_project_dict(project_name, dates, is_p_format=True):
    """
    Helper to construct a project dictionary from name and milestone dates.
    Maps 5 dates to 1-5, 6 dates to 0-5, and other counts sequentially.
    """
    milestones = {}
    prefix = "p" if is_p_format else "c"
    
    if len(dates) == 5:
        keys = [f"{prefix}{i}" for i in range(1, 6)]
    elif len(dates) == 6:
        keys = [f"{prefix}{i}" for i in range(0, 6)]
    else:
        keys = [f"{prefix}{i}" for i in range(len(dates))]
        
    for key, d in zip(keys, dates):
        milestones[key] = d
        
    return {
        "project": project_name,
        "arch": "",
        "milestones": milestones,
        "status": "",
        "owner": ""
    }

def parse_confluence_table(html_content):
    """
    Parses Confluence storage format HTML, finds all tables containing
    milestone milestones (in original format, rowspan format, or new explicit
    milestone format), and extracts all project information.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    
    if not tables:
        logger.warning("No HTML tables found on the page.")
        return []

    all_projects = []

    for table_idx, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue
        
        # Identify the header row
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"])]
        
        # Determine table structure
        has_project = any("專案" in h or "project" in h for h in headers)
        has_milestone_hdr = any("milestone" in h for h in headers)
        has_c0_c5 = any("c0-c5" in h for h in headers)
        has_p0_p5 = any("p0-p5" in h or "p0 - p5" in h for h in headers)
        
        milestone_keys = ["c0", "c1", "c2", "c3", "c4", "c5", "p0", "p1", "p2", "p3", "p4", "p5"]
        has_old_milestones = any(any(k in h for h in headers) for k in milestone_keys)
        
        is_explicit_milestone = has_project and has_milestone_hdr
        is_new_structure = has_project and (has_c0_c5 or has_p0_p5)
        is_old_structure = has_project and has_old_milestones
        
        if not (is_explicit_milestone or is_new_structure or is_old_structure):
            logger.debug(f"Table {table_idx} does not match project table headers. Headers: {headers}")
            continue

        if is_explicit_milestone:
            logger.info(f"Parsing Table {table_idx} as explicit milestone structure.")
            
            # Map headers to column offsets to find status, project, and milestone
            status_idx = -1
            project_idx = -1
            milestone_idx = -1
            owner_idx = -1
            col_offset = 0
            for h_cell in header_row.find_all(["th", "td"]):
                h_text = h_cell.get_text(strip=True).lower()
                colspan = int(h_cell.get("colspan", 1))
                if "status" in h_text or "狀態" in h_text:
                    status_idx = col_offset
                elif "專案" in h_text or "project" in h_text:
                    project_idx = col_offset
                elif "milestone" in h_text:
                    milestone_idx = col_offset
                elif "負責" in h_text or "owner" in h_text:
                    owner_idx = col_offset
                col_offset += colspan
                
            current_project = None
            project_arch = ""
            project_status = ""
            project_owner = ""
            project_milestones = {}
            
            for row in rows[1:]:
                cols = row.find_all(["td", "th"])
                if not cols:
                    continue
                
                # If row has project cell (typically when len(cols) >= 5 or cols[0].has_attr("rowspan"))
                has_project_cell = len(cols) >= 5 or cols[0].has_attr("rowspan")
                
                if has_project_cell:
                    # Save previous project if it exists
                    if current_project and project_milestones:
                        all_projects.append({
                            "project": current_project,
                            "arch": project_arch,
                            "milestones": project_milestones,
                            "status": project_status,
                            "owner": project_owner
                        })
                    
                    # Extract type (e.g. NPDP) and name (e.g. Axx) from project column
                    raw_project = cols[project_idx].get_text(strip=True) if project_idx != -1 else ""
                    lines = [l.strip() for l in cols[project_idx].get_text("\n").split("\n") if l.strip()] if project_idx != -1 else []
                    project_lines = [l for l in lines if "-" not in l]
                    
                    if len(project_lines) >= 2:
                        project_arch = project_lines[0] # Store type (NPDP) as arch
                        current_project = project_lines[1]
                    elif len(project_lines) == 1:
                        project_arch = ""
                        current_project = project_lines[0]
                    else:
                        project_arch = ""
                        current_project = raw_project
                    
                    # Extract milestone label and date
                    m_idx = milestone_idx if milestone_idx != -1 else 1
                    milestone_cell = cols[m_idx] if m_idx < len(cols) else None
                    date_cell = cols[m_idx + 1] if (m_idx + 1) < len(cols) else None
                    
                    # Extract status and owner if their columns were identified
                    project_status = ""
                    project_owner = ""
                    if status_idx != -1 and status_idx < len(cols):
                        status_cell = cols[status_idx]
                        # Look for handy status parameter
                        status_param = status_cell.find("ac:parameter", attrs={"ac:name": "Status"})
                        if status_param:
                            project_status = status_param.get_text(strip=True)
                        else:
                            project_status = status_cell.get_text(strip=True)
                            
                    if owner_idx != -1 and owner_idx < len(cols):
                        project_owner = cols[owner_idx].get_text(strip=True)
                        
                    project_milestones = {}
                else:
                    milestone_cell = cols[0]
                    date_cell = cols[1] if len(cols) > 1 else None
                
                if milestone_cell:
                    # Read milestone label (e.g. "P0", "P1")
                    m_label = milestone_cell.get_text(strip=True).lower().replace(" ", "")
                    
                    # Extract date
                    date_val = None
                    if date_cell:
                        time_tag = date_cell.find("time")
                        if time_tag and time_tag.get("datetime"):
                            date_val = normalize_date(time_tag.get("datetime"))
                        else:
                            date_val = normalize_date(date_cell.get_text(strip=True))
                            
                    if date_val and m_label:
                        project_milestones[m_label] = date_val
                    
            # Save last project of the table
            if current_project and project_milestones:
                all_projects.append({
                    "project": current_project,
                    "arch": project_arch,
                    "milestones": project_milestones,
                    "status": project_status,
                    "owner": project_owner
                })
                
        elif is_new_structure:
            logger.info(f"Parsing Table {table_idx} as new rowspan structure.")
            current_project = None
            project_dates = []
            
            for row in rows[1:]:
                cols = row.find_all(["td", "th"])
                if not cols:
                    continue
                
                first_cell = cols[0]
                has_rowspan = first_cell.has_attr("rowspan")
                
                # Identify if this row starts a new project
                is_new_project = False
                if current_project is None:
                    is_new_project = True
                elif has_rowspan:
                    is_new_project = True
                elif not first_cell.find("time") and not re.search(r"\d{4}[-/.]\d{1,2}", first_cell.get_text(strip=True)):
                    is_new_project = True
                    
                if is_new_project:
                    # Save the previous project if it exists
                    if current_project and project_dates:
                        all_projects.append(create_project_dict(current_project, project_dates, is_p_format=has_p0_p5))
                        
                    current_project = first_cell.get_text(strip=True)
                    project_dates = []
                    date_cell = cols[1] if len(cols) > 1 else None
                else:
                    date_cell = cols[0]
                
                # Extract and normalize date
                if date_cell:
                    date_val = None
                    time_tag = date_cell.find("time")
                    if time_tag and time_tag.get("datetime"):
                        date_val = normalize_date(time_tag.get("datetime"))
                    else:
                        date_val = normalize_date(date_cell.get_text(strip=True))
                    
                    if date_val:
                        project_dates.append(date_val)
                        
            # Save last project in table
            if current_project and project_dates:
                all_projects.append(create_project_dict(current_project, project_dates, is_p_format=has_p0_p5))
                
        elif is_old_structure:
            logger.info(f"Parsing Table {table_idx} as original flat structure.")
            # Map column names to indices
            indices = {
                "project": -1, "arch": -1,
                "c0": -1, "c1": -1, "c2": -1, "c3": -1, "c4": -1, "c5": -1,
                "p0": -1, "p1": -1, "p2": -1, "p3": -1, "p4": -1, "p5": -1,
                "status": -1, "owner": -1
            }
            
            for i, h in enumerate(headers):
                if "project" in h or "專案" in h:
                    indices["project"] = i
                elif "arch" in h or "架構" in h:
                    indices["arch"] = i
                elif "status" in h or "狀態" in h or "說明" in h:
                    indices["status"] = i
                elif "owner" in h or "負責" in h:
                    indices["owner"] = i
                else:
                    # Check other keys
                    for k in milestone_keys:
                        if k in h:
                            indices[k] = i

            for row in rows[1:]:
                cols = row.find_all(["td", "th"])
                if not cols:
                    continue
                
                def get_col_val(key):
                    idx = indices[key]
                    if idx != -1 and idx < len(cols):
                        return cols[idx].get_text(" ", strip=True)
                    return ""

                project_name = get_col_val("project")
                if not project_name:
                    continue
                    
                arch = get_col_val("arch")
                status = get_col_val("status")
                owner = get_col_val("owner")
                
                milestones = {}
                for k in milestone_keys:
                    raw_val = get_col_val(k)
                    norm_val = normalize_date(raw_val)
                    if norm_val:
                        milestones[k] = norm_val

                all_projects.append({
                    "project": project_name,
                    "arch": arch,
                    "milestones": milestones,
                    "status": status,
                    "owner": owner
                })
                
    logger.info(f"Successfully parsed {len(all_projects)} projects from the milestones table(s).")
    return all_projects
