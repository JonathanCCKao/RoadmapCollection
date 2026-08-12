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
    If multiple dates exist (e.g. a range), returns the LAST one.
    """
    if not text:
        return None
    
    text = text.strip()
    matches = list(DATE_RE.finditer(text))
    if not matches:
        return None
        
    match = matches[-1]
    year, month, day = match.groups()
    try:
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

def extract_milestones_from_cell(cell, parent_table):
    """
    Extracts a dictionary of milestone_label -> date_str from a cell.
    Supports task-lists, bullet lists with time tags, and text fallbacks.
    """
    milestones = {}
    if not cell:
        return milestones
        
    milestone_keys = ["c0", "c1", "c2", "c3", "c4", "c5", "p0", "p1", "p2", "p3", "p4", "p5"]
        
    # 1. Check if there is an ac:task-list
    tasks = cell.find_all("ac:task")
    if tasks:
        for task in tasks:
            task_body = task.find("ac:task-body")
            if not task_body:
                continue
            text = task_body.get_text(" ", strip=True)
            label_match = re.search(r"\b([cp][0-5])\b", text, re.IGNORECASE)
            if not label_match:
                continue
            label = label_match.group(1).lower()
            
            # Find date in status macro parameter title
            date_val = None
            status_title = task_body.find("ac:parameter", attrs={"ac:name": "title"})
            if status_title:
                date_val = normalize_date(status_title.get_text(strip=True))
            if not date_val:
                date_val = normalize_date(text)
            if date_val:
                milestones[label] = date_val
        return milestones

    # 2. Check if there are li items
    li_items = cell.find_all("li")
    if li_items:
        for li in li_items:
            # Check if this li belongs to a nested table (skip it)
            if li.find_parent("table") != parent_table:
                continue
            text = li.get_text(" ", strip=True)
            label_match = re.search(r"\b([cp][0-5])\b", text, re.IGNORECASE)
            if not label_match:
                continue
            label = label_match.group(1).lower()
            
            # Find date
            date_val = None
            time_tags = li.find_all("time")
            if time_tags:
                dates = [normalize_date(t.get("datetime")) for t in time_tags if t.get("datetime")]
                dates = [d for d in dates if d]
                if dates:
                    date_val = dates[-1]
            if not date_val:
                date_val = normalize_date(text)
            if date_val:
                milestones[label] = date_val
        return milestones

    # 3. Fallback to line-by-line parsing of the cell
    lines = cell.get_text("\n").split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        label_match = re.search(r"\b([cp][0-5])\b", line, re.IGNORECASE)
        if not label_match:
            continue
        label = label_match.group(1).lower()
        date_val = normalize_date(line)
        if date_val:
            milestones[label] = date_val
            
    return milestones

def parse_confluence_table(html_content):
    """
    Parses Confluence HTML, finds all tables containing milestone roadmaps,
    and extracts all project information with support for multiple formats
    and nested table skipping.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    
    if not tables:
        logger.warning("No HTML tables found on the page.")
        return []

    all_projects = []
    milestone_keys = ["c0", "c1", "c2", "c3", "c4", "c5", "p0", "p1", "p2", "p3", "p4", "p5"]

    for table_idx, table in enumerate(tables):
        # Filter rows to only those belonging directly to this table
        all_trs = table.find_all("tr")
        rows = [tr for tr in all_trs if tr.find_parent("table") == table]
        if not rows:
            continue
        
        # Identify the header row
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"], recursive=False)]
        
        # Determine table structure
        has_project = any("專案" in h or "project" in h for h in headers)
        has_milestone_hdr = any("milestone" in h for h in headers)
        has_c0_c5 = any("c0-c5" in h for h in headers)
        has_p0_p5 = any("p0-p5" in h or "p0 - p5" in h for h in headers)
        
        has_old_milestones = any(any(k in h for h in headers) for k in milestone_keys)
        
        is_explicit_milestone = has_project and has_milestone_hdr
        is_new_structure = has_project and (has_c0_c5 or has_p0_p5)
        is_old_structure = has_project and has_old_milestones
        
        if not (is_explicit_milestone or is_new_structure or is_old_structure):
            logger.debug(f"Table {table_idx} does not match project table headers. Headers: {headers}")
            continue

        if is_explicit_milestone:
            logger.info(f"Parsing Table {table_idx} as explicit milestone structure.")
            
            # Map headers to column offsets
            status_idx = -1
            project_idx = -1
            milestone_idx = -1
            owner_idx = -1
            col_offset = 0
            for h_cell in header_row.find_all(["th", "td"], recursive=False):
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
                cols = row.find_all(["td", "th"], recursive=False)
                if not cols:
                    continue
                
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
                    
                    # Extract project info from project column
                    cell_text = cols[project_idx].get_text("\n") if project_idx != -1 and project_idx < len(cols) else ""
                    lines = [l.strip() for l in cell_text.split("\n") if l.strip()]
                    project_lines = [l for l in lines if not re.match(r"^[-=\s]+$", l)]
                    
                    if len(project_lines) >= 2:
                        project_arch = project_lines[0]
                        current_project = " ".join(project_lines[1:])
                    elif len(project_lines) == 1:
                        project_arch = ""
                        current_project = project_lines[0]
                    else:
                        current_project = cols[project_idx].get_text(strip=True) if project_idx != -1 and project_idx < len(cols) else ""
                        project_arch = ""
                    
                    m_idx = milestone_idx if milestone_idx != -1 else 1
                    milestone_cell = cols[m_idx] if m_idx < len(cols) else None
                    date_cell = cols[m_idx + 1] if (m_idx + 1) < len(cols) else None
                    
                    # Extract status and owner
                    project_status = ""
                    project_owner = ""
                    if status_idx != -1 and status_idx < len(cols):
                        status_cell = cols[status_idx]
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
                    # Format B: multiple milestones parsed inside this cell
                    extracted = extract_milestones_from_cell(milestone_cell, table)
                    
                    # Format A: fallback (milestone label in this cell, date in next cell)
                    if not extracted:
                        m_label = milestone_cell.get_text(strip=True).lower().replace(" ", "")
                        date_val = None
                        if date_cell:
                            time_tag = date_cell.find("time")
                            if time_tag and time_tag.get("datetime"):
                                date_val = normalize_date(time_tag.get("datetime"))
                            else:
                                date_val = normalize_date(date_cell.get_text(strip=True))
                        if date_val and m_label:
                            clean_label = None
                            for k in milestone_keys:
                                if k in m_label:
                                    clean_label = k
                                    break
                            if clean_label:
                                extracted[clean_label] = date_val
                            else:
                                extracted[m_label] = date_val
                                
                    project_milestones.update(extracted)
                    
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
                cols = row.find_all(["td", "th"], recursive=False)
                if not cols:
                    continue
                
                first_cell = cols[0]
                has_rowspan = first_cell.has_attr("rowspan")
                
                is_new_project = False
                if current_project is None:
                    is_new_project = True
                elif has_rowspan:
                    is_new_project = True
                elif not first_cell.find("time") and not re.search(r"\d{4}[-/.]\d{1,2}", first_cell.get_text(strip=True)):
                    is_new_project = True
                    
                if is_new_project:
                    if current_project and project_dates:
                        all_projects.append(create_project_dict(current_project, project_dates, is_p_format=has_p0_p5))
                        
                    current_project = first_cell.get_text(strip=True)
                    project_dates = []
                    date_cell = cols[1] if len(cols) > 1 else None
                else:
                    date_cell = cols[0]
                
                if date_cell:
                    date_val = None
                    time_tag = date_cell.find("time")
                    if time_tag and time_tag.get("datetime"):
                        date_val = normalize_date(time_tag.get("datetime"))
                    else:
                        date_val = normalize_date(date_cell.get_text(strip=True))
                    
                    if date_val:
                        project_dates.append(date_val)
                        
            if current_project and project_dates:
                all_projects.append(create_project_dict(current_project, project_dates, is_p_format=has_p0_p5))
                
        elif is_old_structure:
            logger.info(f"Parsing Table {table_idx} as original flat structure.")
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
                    for k in milestone_keys:
                        if k in h:
                            indices[k] = i

            for row in rows[1:]:
                cols = row.find_all(["td", "th"], recursive=False)
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
                
    logger.info(f"Successfully parsed {len(all_projects)} projects from the Confluence table(s).")
    return all_projects
