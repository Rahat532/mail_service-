from string import Template

def render_template(template_str: str, data: dict) -> str:
    """
    Render a string template with data.
    Uses safe_substitute to avoid crashing on missing keys.
    """
    if template_str is None:
        return ""
    # Use string.Template for safer substitution (using $var or ${var}) 
    # OR standard f-string/format method (using {var})? 
    # Requirement said: {email}, {name}. So we use str.format() 
    # but we need to handle missing keys gracefully.
    
    class SafeDict(dict):
        def __missing__(self, key):
            return f"{{{key}}}" # Return placeholder if missing

    return template_str.format_map(SafeDict(data))
