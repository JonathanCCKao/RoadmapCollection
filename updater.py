import re
import json
import logging

logger = logging.getLogger(__name__)

def update_html_body(existing_body, chart_code, mode="plantuml", insert_position="top", projects_data=None):
    """
    Finds and replaces an existing <ac:structured-macro> block (either mermaid or plantuml)
    in the Confluence page storage format. If none is found, it prepends or
    appends the block according to `insert_position`.
    Also handles the creation/replacement of the 'Roadmap Data Source' expand macro containing JSON.
    """
    macro_name = "plantuml" if mode == "plantuml" else "mermaid"
    other_macro = "mermaid" if mode == "plantuml" else "plantuml"

    new_macro = (
        f'<ac:structured-macro ac:name="{macro_name}">\n'
        f'  <ac:plain-text-body><![CDATA[\n'
        f'{chart_code}\n'
        f'  ]]></ac:plain-text-body>\n'
        f'</ac:structured-macro>'
    )

    # Regex patterns for finding macros
    target_pattern = re.compile(
        f'<ac:structured-macro\\s+[^>]*ac:name="{macro_name}"[^>]*>.*?</ac:structured-macro>', 
        re.DOTALL
    )
    other_pattern = re.compile(
        f'<ac:structured-macro\\s+[^>]*ac:name="{other_macro}"[^>]*>.*?</ac:structured-macro>', 
        re.DOTALL
    )

    # First, handle replacing or prepending/appending the chart macro
    if target_pattern.search(existing_body):
        logger.info(f"Found existing {macro_name} macro block. Replacing it.")
        temp_body = target_pattern.sub(new_macro, existing_body)
    elif other_pattern.search(existing_body):
        logger.info(f"Found existing {other_macro} macro block (different mode). Overwriting with {macro_name}.")
        temp_body = other_pattern.sub(new_macro, existing_body)
    else:
        logger.info(f"No existing {macro_name} or {other_macro} macro block found. Inserting at the {insert_position}.")
        if insert_position == "bottom":
            temp_body = existing_body.rstrip() + "\n\n" + new_macro
        else:
            temp_body = new_macro + "\n\n" + existing_body.lstrip()

    # Next, handle the Roadmap Data Source expand macro
    if projects_data is not None:
        json_str = json.dumps(projects_data, indent=2, ensure_ascii=False)
        new_expand = (
            '<ac:structured-macro ac:name="expand">\n'
            '  <ac:parameter ac:name="title">Roadmap Data Source</ac:parameter>\n'
            '  <ac:rich-text-body>\n'
            '    <p>以下為解析後的專案時程 JSON 原始資料：</p>\n'
            '    <ac:structured-macro ac:name="code">\n'
            '      <ac:parameter ac:name="language">json</ac:parameter>\n'
            '      <ac:plain-text-body><![CDATA['
            f'{json_str}'
            ']]></ac:plain-text-body>\n'
            '    </ac:structured-macro>\n'
            '  </ac:rich-text-body>\n'
            '</ac:structured-macro>'
        )

        # Regex to locate expand macro with title "Roadmap Data Source"
        # We search for <ac:structured-macro ac:name="expand"> that has the specific title parameter
        expand_pattern = re.compile(
            r'<ac:structured-macro\s+[^>]*ac:name="expand"[^>]*>'
            r'(?:(?!</ac:structured-macro>).)*?'
            r'<ac:parameter\s+[^>]*ac:name="title"[^>]*>\s*Roadmap\s+Data\s+Source\s*</ac:parameter>'
            r'.*?'
            r'</ac:rich-text-body>\s*'
            r'</ac:structured-macro>',
            re.DOTALL | re.IGNORECASE
        )

        if expand_pattern.search(temp_body):
            logger.info("Found existing Roadmap Data Source expand macro. Replacing it.")
            updated_body = expand_pattern.sub(new_expand, temp_body)
        else:
            logger.info("No existing Roadmap Data Source expand macro found. Inserting below the chart.")
            # Insert the new expand macro immediately below the newly written new_macro
            updated_body = temp_body.replace(new_macro, new_macro + "\n\n" + new_expand, 1)
    else:
        updated_body = temp_body

    return updated_body
