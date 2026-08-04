import logging

logger = logging.getLogger(__name__)

MILESTONE_LABELS = {
    "c0": "C0", "c1": "C1", "c2": "C2", "c3": "C3", "c4": "C4", "c5": "C5",
    "p0": "P0", "p1": "P1", "p2": "P2", "p3": "P3", "p4": "P4", "p5": "P5"
}

MILESTONE_COLORS = {
    "c0": "#EBF5FB",  # Very light ice blue
    "c1": "#AED6F1",  # Soft sky blue
    "c2": "#5DADE2",  # Business blue
    "c3": "#2E86C1",  # Steel blue
    "c4": "#1B4F72",  # Deep navy blue
    "c5": "#58D68D",  # Soft emerald green (GA / Launch)
    "p0": "#EBF5FB",  # Very light ice blue
    "p1": "#AED6F1",  # Soft sky blue
    "p2": "#5DADE2",  # Business blue
    "p3": "#2E86C1",  # Steel blue
    "p4": "#1B4F72",  # Deep navy blue
    "p5": "#58D68D"   # Soft emerald green (GA / Launch)
}

MILESTONE_TEXT_COLORS = {
    "c0": "#1F4E79",  # Deep Navy (for ice blue background)
    "c1": "#1F4E79",  # Deep Navy (for sky blue background)
    "c2": "#1F4E79",  # Deep Navy (for business blue background)
    "c3": "#FFFFFF",  # White (for steel blue background)
    "c4": "#FFFFFF",  # White (for deep navy background)
    "c5": "#1F4E79",  # Deep Navy (for emerald green background)
    "p0": "#1F4E79",
    "p1": "#1F4E79",
    "p2": "#1F4E79",
    "p3": "#FFFFFF",
    "p4": "#FFFFFF",
    "p5": "#1F4E79"
}

def generate_plantuml_gantt(projects, scale="quarterly", zoom=3, update_time=None):
    """
    Generates a PlantUML Gantt chart with milestones represented as contiguous
    colored tasks displaying on the same row.
    """
    if not update_time:
        from datetime import datetime
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Find the earliest date among all milestones to define the project starts date
    all_dates = []
    for p in projects:
        for d in p["milestones"].values():
            if d:
                all_dates.append(d)
                
    earliest_date = min(all_dates) if all_dates else None

    lines = [
        "@startgantt",
        f"right header <font color=\"#1F4E79\"><b>最後更新時間: {update_time}</b></font>",
        "title <size:20>交換機產品Roadmap</size>"
    ]
    
    if earliest_date:
        lines.append(f"project starts {earliest_date}")
    
    # Set the timeline scale with zoom
    lines.append(f"projectscale {scale} zoom {zoom}")

    # Add vertical line for today (current time position)
    lines.append("today is colored in #E74C3C")

    # Add NOW milestone at the current time position (aligns with today line)
    if update_time:
        today_str = update_time.split()[0]
    else:
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"[NOW] happens {today_str}")
    lines.append("[NOW] is colored in #E74C3C")

    # Add soft background colors for different years to distinguish them (no black)
    year_backgrounds = [
        "#FDF2E9",  # 1st Year: Soft pastel peach
        "#E8F8F5",  # 2nd Year: Soft pastel mint
        "#FEF9E7",  # 3rd Year: Soft pastel cream
        "#EBF5FB"   # 4th Year: Soft pastel blue
    ]

    if all_dates:
        years = sorted(list(set(int(d.split("-")[0]) for d in all_dates)))
        for idx, yr in enumerate(years):
            color = year_backgrounds[idx % len(year_backgrounds)]
            # Highlight the entire year
            lines.append(f"{yr}-01-01 to {yr}-12-31 are colored in {color}")

    # Add subtle vertical year separator lines
    if all_dates:
        years = sorted(list(set(int(d.split("-")[0]) for d in all_dates)))
        for yr in range(min(years) + 1, max(years) + 1):
            boundary_date = f"{yr}-01-01"
            lines.append(f"{boundary_date} is colored in #CCD1D1")

    for p in projects:
        project_name = p["project"]
        arch = p["arch"]
        milestones = p["milestones"]

        # Determine status-based color for the project name (default to elegant Deep Navy #1F4E79)
        status_str = p.get("status", "").upper() if p.get("status") else ""
        if "NEED SUPPORT" in status_str or "🔴" in status_str or "阻礙" in status_str or "嚴重" in status_str:
            name_color = "#922B21"  # Deep Red (Need Support / Red status)
        elif "CATCHING UP" in status_str or "🟡" in status_str or "警告" in status_str or "延遲" in status_str:
            name_color = "#B9770E"  # Dark Amber (Catching Up / Yellow status)
        elif "ON TRACK" in status_str or "🟢" in status_str or "正常" in status_str or "健康" in status_str:
            name_color = "#1E8449"  # Forest Green (On Track / Green status)
        else:
            name_color = "#1F4E79"  # Default Deep Navy Blue

        # Separator header (with project name in bold and colored)
        section_title = f"<font color=\"{name_color}\">**{project_name} ({arch})**</font>" if arch else f"<font color=\"{name_color}\">**{project_name}**</font>"
        lines.append(f"\n-- {section_title} --")

        # Get list of valid milestone keys that actually have dates, sorted
        milestone_keys = ["c0", "c1", "c2", "c3", "c4", "c5", "p0", "p1", "p2", "p3", "p4", "p5"]
        valid_keys = [k for k in milestone_keys if milestones.get(k)]
        
        first_task_id = None
        
        for i, key in enumerate(valid_keys):
            date_val = milestones[key]
            
            # Determine end date based on next milestone start date
            if i + 1 < len(valid_keys):
                next_key = valid_keys[i + 1]
                end_val = milestones[next_key]
                time_def = f"starts {date_val} and ends {end_val}"
                label = key.upper()
            else:
                # The last milestone (usually C5 GA / P5) has a small fixed duration
                time_def = f"starts {date_val} and lasts 3 days"
                # Append project name to the label so it displays on the right side
                label = f"{key.upper()} ({project_name})"
                
            task_id = f"{project_name}_{key}"
            color = MILESTONE_COLORS.get(key, "#3498DB")
            text_color = MILESTONE_TEXT_COLORS.get(key, "#1F4E79")
            display_label = f"<color:{text_color}><b>{label}</b></color>"
            
            # Define task: [C1] as [project_c1] starts YYYY-MM-DD and ends YYYY-MM-DD
            lines.append(f"[{display_label}] as [{task_id}] {time_def}")
            lines.append(f"[{task_id}] is colored in {color}")
            
            # Align all tasks of this project on the same horizontal row
            if first_task_id is None:
                first_task_id = task_id
            else:
                lines.append(f"[{task_id}] displays on same row as [{first_task_id}]")

    lines.append("@endgantt")
    logger.info(f"Generated PlantUML Gantt code successfully. Project starts at: {earliest_date}, scale: {scale}, zoom: {zoom}")
    return "\n".join(lines)

def generate_mermaid_gantt(projects):
    """
    Generates a Mermaid.js Gantt chart from a list of project milestone dicts.
    """
    lines = [
        "gantt",
        "    dateFormat  YYYY-MM-DD",
        "    title 交換機產品Roadmap",
        "    axisFormat  %Y-%m"
    ]

    for p_idx, p in enumerate(projects):
        project_name = p["project"]
        arch = p["arch"]
        milestones = p["milestones"]

        # Form section header
        if arch:
            lines.append(f"\n    section {project_name} ({arch})")
        else:
            lines.append(f"\n    section {project_name}")

        # Render valid milestones
        milestone_keys = ["c0", "c1", "c2", "c3", "c4", "c5"]
        for key in milestone_keys:
            date_val = milestones.get(key)
            if not date_val:
                continue
            
            label = MILESTONE_LABELS.get(key, key.upper())
            milestone_id = f"p{p_idx}_{key}"
            
            # Format: <label> :milestone, <id>, <date>, 0d
            lines.append(f"    {label:<16} :milestone, {milestone_id}, {date_val}, 0d")

    mermaid_code = "\n".join(lines)
    logger.info("Generated Mermaid Gantt code successfully.")
    return mermaid_code

def generate_chart(projects, mode="plantuml", scale="quarterly", zoom=3, update_time=None):
    """
    Dispatch function to generate either PlantUML or Mermaid Gantt chart code.
    """
    if mode == "plantuml":
        return generate_plantuml_gantt(projects, scale=scale, zoom=zoom, update_time=update_time)
    return generate_mermaid_gantt(projects)
