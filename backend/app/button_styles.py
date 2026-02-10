"""Button style templates for different WordPress sites.

Provides a modular system for customizing button appearance per site.
Each style defines CSS properties and hover effects.
"""

from typing import Dict, Any


# Predefined button style templates
BUTTON_STYLES = {
    "default": {
        "name": "Default Pink Border",
        "description": "Pink border with white background, blue hover effect",
        "css": {
            "padding": "15px 30px",
            "border": "3px solid #ff216d",
            "border-radius": "15px",
            "background-color": "white",
            "color": "#ff216d",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box"
        },
        "hover": {
            "border-color": "#42a2f6",
            "color": "#42a2f6"
        }
    },
    "gradient_blue": {
        "name": "Gradient Blue",
        "description": "Blue gradient background with white text",
        "css": {
            "padding": "15px 30px",
            "border": "none",
            "border-radius": "12px",
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "color": "white",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box",
            "box-shadow": "0 4px 15px rgba(102, 126, 234, 0.4)"
        },
        "hover": {
            "transform": "translateY(-2px)",
            "box-shadow": "0 6px 20px rgba(102, 126, 234, 0.6)"
        }
    },
    "solid_green": {
        "name": "Solid Green",
        "description": "Solid green background with white text",
        "css": {
            "padding": "15px 30px",
            "border": "none",
            "border-radius": "10px",
            "background-color": "#10b981",
            "color": "white",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box"
        },
        "hover": {
            "background-color": "#059669",
            "transform": "scale(1.02)"
        }
    },
    "outline_orange": {
        "name": "Orange Outline",
        "description": "Orange border outline with fill on hover",
        "css": {
            "padding": "15px 30px",
            "border": "3px solid #f97316",
            "border-radius": "8px",
            "background-color": "transparent",
            "color": "#f97316",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box"
        },
        "hover": {
            "background-color": "#f97316",
            "color": "white"
        }
    },
    "gradient_sunset": {
        "name": "Sunset Gradient",
        "description": "Warm sunset gradient from orange to pink",
        "css": {
            "padding": "15px 30px",
            "border": "none",
            "border-radius": "25px",
            "background": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "color": "white",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box",
            "box-shadow": "0 4px 15px rgba(245, 87, 108, 0.4)"
        },
        "hover": {
            "box-shadow": "0 6px 25px rgba(245, 87, 108, 0.6)",
            "transform": "translateY(-2px)"
        }
    },
    "modern_dark": {
        "name": "Modern Dark",
        "description": "Dark background with subtle border",
        "css": {
            "padding": "15px 30px",
            "border": "2px solid #374151",
            "border-radius": "12px",
            "background-color": "#1f2937",
            "color": "white",
            "font-size": "18px",
            "font-weight": "600",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box"
        },
        "hover": {
            "background-color": "#374151",
            "border-color": "#6b7280"
        }
    },
    "neon_purple": {
        "name": "Neon Purple",
        "description": "Vibrant purple with neon glow effect",
        "css": {
            "padding": "15px 30px",
            "border": "2px solid #a855f7",
            "border-radius": "15px",
            "background-color": "#7c3aed",
            "color": "white",
            "font-size": "18px",
            "font-weight": "bold",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box",
            "box-shadow": "0 0 20px rgba(168, 85, 247, 0.5)"
        },
        "hover": {
            "box-shadow": "0 0 30px rgba(168, 85, 247, 0.8)",
            "background-color": "#6d28d9"
        }
    },
    "minimal_blue": {
        "name": "Minimal Blue",
        "description": "Clean minimal design with subtle blue",
        "css": {
            "padding": "15px 30px",
            "border": "2px solid #3b82f6",
            "border-radius": "8px",
            "background-color": "#eff6ff",
            "color": "#1e40af",
            "font-size": "18px",
            "font-weight": "600",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "width": "100%",
            "box-sizing": "border-box"
        },
        "hover": {
            "background-color": "#dbeafe",
            "border-color": "#2563eb"
        }
    },
    "popbies_split_layout": {
        "name": "Popbies Split Layout",
        "description": "Two-column layout with text on left and teal button on right, like popbies.com",
        "layout_type": "split",  # Special flag for split layout
        "container": {
            "padding": "15px 20px",
            "background-color": "#f3f4f6",
            "border-radius": "12px",
            "display": "flex",
            "align-items": "center",
            "justify-content": "space-between",
            "margin": "10px 0",
            "box-sizing": "border-box"
        },
        "label": {
            "color": "#1f2937",
            "font-size": "16px",
            "font-weight": "600",
            "margin": "0"
        },
        "css": {
            "padding": "12px 35px",
            "border": "none",
            "border-radius": "8px",
            "background-color": "#14b8a6",
            "color": "white",
            "font-size": "16px",
            "font-weight": "600",
            "text-decoration": "none",
            "text-align": "center",
            "transition": "all 0.3s",
            "display": "inline-block",
            "box-sizing": "border-box",
            "min-width": "120px"
        },
        "hover": {
            "background-color": "#0d9488",
            "transform": "scale(1.02)"
        },
        "disabled": {
            "background-color": "#9ca3af",
            "color": "#e5e7eb",
            "cursor": "not-allowed"
        }
    }
}


def get_button_style(style_name: str) -> Dict[str, Any]:
    """Get button style configuration by name.
    
    Args:
        style_name: Name of the style template (e.g., 'default', 'gradient_blue')
        
    Returns:
        Dict containing style configuration with 'css' and 'hover' properties
    """
    return BUTTON_STYLES.get(style_name, BUTTON_STYLES["default"])


def get_all_button_styles() -> Dict[str, Dict[str, Any]]:
    """Get all available button style templates."""
    return BUTTON_STYLES


def _title_has_leading_number(title: str) -> bool:
    """Check if title already starts with a number pattern.
    
    Detects patterns like: "01.", "1.", "1+", "10.", "15.", etc.
    
    Args:
        title: Button title text
        
    Returns:
        True if title starts with a number pattern, False otherwise
    """
    import re
    # Match patterns: "01.", "1.", "1+", "10.", etc. at the start
    pattern = r'^\s*\d+[\.\+\-\)\:]\s*'
    return bool(re.match(pattern, title.strip()))


def generate_button_html(link: Dict[str, Any], style_name: str = "default", numbering_mode: str = "auto") -> str:
    """Generate button HTML with specified style.
    
    Args:
        link: Dict with 'url', 'title', 'order', and optional 'target'
        style_name: Name of the button style to apply
        numbering_mode: How to handle button numbering:
            - "auto": Only add number if title doesn't already have one (default)
            - "always": Always add order number prefix
            - "never": Never add order number prefix
        
    Returns:
        HTML string for the button within a WordPress column block
    """
    style = get_button_style(style_name)
    target = link.get('target', '_blank')
    rel_attr = ' rel="noopener noreferrer"' if target == '_blank' else ''
    
    # Check if this is a split layout style
    if style.get("layout_type") == "split":
        return _generate_split_layout_html(link, style, target, rel_attr, numbering_mode)
    
    # Standard button layout (existing code)
    # Convert CSS dict to inline style string
    css_string = "; ".join([f"{k}: {v}" for k, v in style["css"].items()])
    
    # Convert hover dict to onmouseover/onmouseout handlers
    hover_over = "; ".join([f"this.style.{k.replace('-', '')} = '{v}'" for k, v in style["hover"].items()])
    hover_out = "; ".join([f"this.style.{k.replace('-', '')} = '{style['css'].get(k, '')}' " for k in style["hover"].keys()])
    
    # Determine button text based on numbering mode
    title = link['title']
    if numbering_mode == "always":
        # Always add order number
        button_text = f"{link['order']:02d}. {title}"
    elif numbering_mode == "never":
        # Never add order number
        button_text = title
    else:  # "auto" (default)
        # Only add order number if title doesn't already have one
        if _title_has_leading_number(title):
            button_text = title
        else:
            button_text = f"{link['order']:02d}. {title}"
    
    button_html = f'''<!-- wp:column {{"width":"33.33%"}} -->
<div class="wp-block-column" style="flex-basis:33.33%">
    <div style="margin: 15px 0;">
        <a href="{link['url']}" target="{target}"{rel_attr} style="{css_string}" onmouseover="{hover_over}" onmouseout="{hover_out}">{button_text}</a>
    </div>
</div>
<!-- /wp:column -->'''
    
    return button_html


def _generate_split_layout_html(link: Dict[str, Any], style: Dict[str, Any], target: str, rel_attr: str, numbering_mode: str) -> str:
    """Generate split layout HTML (text on left, button on right).
    
    Args:
        link: Dict with 'url', 'title', 'order', and optional 'target'
        style: Style configuration dict
        target: Link target attribute
        rel_attr: Link rel attribute
        numbering_mode: How to handle button numbering
        
    Returns:
        HTML string for the split layout button
    """
    # Container styles
    container_string = "; ".join([f"{k}: {v}" for k, v in style["container"].items()])
    
    # Label styles
    label_string = "; ".join([f"{k}: {v}" for k, v in style["label"].items()])
    
    # Button styles
    css_string = "; ".join([f"{k}: {v}" for k, v in style["css"].items()])
    
    # Convert hover dict to onmouseover/onmouseout handlers
    hover_over = "; ".join([f"this.style.{css_property_to_js(k)} = '{v}'" for k, v in style["hover"].items()])
    hover_out = "; ".join([f"this.style.{css_property_to_js(k)} = '{style['css'].get(k, '')}'" for k in style["hover"].keys()])
    
    # Determine label text (left side)
    title = link['title']
    if numbering_mode == "always":
        label_text = f"{link['order']:02d}. {title}"
    elif numbering_mode == "never":
        label_text = title
    else:  # "auto" (default)
        if _title_has_leading_number(title):
            label_text = title
        else:
            label_text = f"{link['order']:02d}. {title}"
    
    # Button text (right side) - typically "Claim" or custom
    button_text = link.get('button_text', 'Claim')
    
    # Disabled/claimed styles from the style config
    disabled_css = style.get('disabled', {})
    disabled_string = "; ".join([f"{k}: {v}" for k, v in disabled_css.items()])
    
    # Generate unique ID for this button based on URL (for localStorage)
    import hashlib
    button_id = hashlib.md5(link['url'].encode()).hexdigest()[:12]
    
    # JavaScript for claim functionality with localStorage persistence
    onclick_js = f"""
    (function(btn) {{
        var storageKey = 'claimed_' + '{button_id}';
        
        // Check if already claimed
        if (localStorage.getItem(storageKey) === 'true') {{
            return false;
        }}
        
        // Mark as claimed
        setTimeout(function() {{
            btn.textContent = 'Claimed';
            btn.style.cssText = '{disabled_string}';
            btn.style.pointerEvents = 'none';
            localStorage.setItem(storageKey, 'true');
        }}, 100);
        
        return true;
    }})(this)
    """.replace('\n', ' ').strip()
    
    # Check claimed state on page load script
    onload_check = f"""
    (function() {{
        var storageKey = 'claimed_{button_id}';
        if (localStorage.getItem(storageKey) === 'true') {{
            var btn = document.querySelector('[data-btn-id=\\"{button_id}\\"]');
            if (btn) {{
                btn.textContent = 'Claimed';
                btn.style.cssText = '{disabled_string}';
                btn.style.pointerEvents = 'none';
            }}
        }}
    }})();
    """
    
    button_html = f'''<!-- wp:column {{"width":"100%"}} -->
<div class="wp-block-column" style="flex-basis:100%">
    <div style="{container_string}">
        <span style="{label_string}">{label_text}</span>
        <a href="{link['url']}" target="{target}"{rel_attr} data-btn-id="{button_id}" style="{css_string}" onmouseover="if(this.textContent!=='Claimed'){{{hover_over}}}" onmouseout="if(this.textContent!=='Claimed'){{{hover_out}}}" onclick="{onclick_js}">{button_text}</a>
    </div>
</div>
<!-- /wp:column -->
<script>{onload_check}</script>'''
    
    return button_html


def css_property_to_js(css_property: str) -> str:
    """Convert CSS property name to JavaScript style property.
    
    Example: 'border-color' -> 'borderColor'
    """
    parts = css_property.split('-')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])
