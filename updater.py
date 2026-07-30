import re
import logging

logger = logging.getLogger(__name__)

def update_html_body(existing_body, chart_code, mode="plantuml", insert_position="top"):
    """
    Finds and replaces an existing <ac:structured-macro> block (either mermaid or plantuml)
    in the Confluence page storage format. If none is found, it prepends or
    appends the block according to `insert_position`.
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

    if target_pattern.search(existing_body):
        logger.info(f"Found existing {macro_name} macro block. Replacing it.")
        updated_body = target_pattern.sub(new_macro, existing_body)
    elif other_pattern.search(existing_body):
        logger.info(f"Found existing {other_macro} macro block (different mode). Overwriting with {macro_name}.")
        updated_body = other_pattern.sub(new_macro, existing_body)
    else:
        logger.info(f"No existing {macro_name} or {other_macro} macro block found. Inserting at the {insert_position}.")
        if insert_position == "bottom":
            updated_body = existing_body.rstrip() + "\n\n" + new_macro
        else:
            updated_body = new_macro + "\n\n" + existing_body.lstrip()

    return updated_body
