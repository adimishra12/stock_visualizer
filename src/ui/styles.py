"""Dynamic CSS generation and theme persistence bridge.

Provides cohesive styling for both Light mode (default) and Dark mode,
applying tokens to Streamlit native components and custom fintech classes.
"""

from src.config import get_theme


def get_theme_css(theme_name: str) -> str:
    """Generate dynamic CSS injecting :root tokens and fintech component classes."""
    theme = get_theme(theme_name)
    is_dark = theme["name"] == "dark"

    # Tab active colors and widget accents
    tab_active_bg = "rgba(109, 40, 217, 0.08)" if not is_dark else "rgba(139, 92, 246, 0.15)"
    badge_pos_bg = "rgba(16, 185, 129, 0.12)" if not is_dark else "rgba(52, 211, 153, 0.15)"
    badge_neg_bg = "rgba(244, 63, 94, 0.12)" if not is_dark else "rgba(251, 113, 133, 0.15)"
    badge_warn_bg = "rgba(245, 158, 11, 0.12)" if not is_dark else "rgba(251, 191, 36, 0.15)"
    input_focus_ring = "rgba(109, 40, 217, 0.2)" if not is_dark else "rgba(139, 92, 246, 0.25)"
    input_bg = "#FFFFFF" if not is_dark else "#0F172A"
    input_border = "#E5E7EB" if not is_dark else "#334155"
    input_text = "#111827" if not is_dark else "#F8FAFC"
    input_placeholder = "#64748B" if not is_dark else "#94A3B8"
    input_focus_border = "#6D28D9" if not is_dark else "#8B5CF6"
    sb_btn_bg = "#FFFFFF" if not is_dark else "#1E293B"
    sb_btn_border = "#E5E7EB" if not is_dark else "#334155"
    sb_btn_icon = "#111827" if not is_dark else "#F8FAFC"

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --bg-primary: {theme['bg_primary']};
        --bg-secondary: {theme['bg_secondary']};
        --bg-card: {theme['bg_card']};
        --text-primary: {theme['text_primary']};
        --text-secondary: {theme['text_secondary']};
        --accent-primary: {theme['accent_primary']};
        --accent-secondary: {theme['accent_secondary']};
        --color-positive: {theme['positive']};
        --color-negative: {theme['negative']};
        --color-warning: {theme['warning']};
        --border-color: {theme['border']};
        --card-shadow: {theme['card_shadow']};
        --card-hover-shadow: {theme['card_hover_shadow']};
        --input-bg: {input_bg};
        --input-border: {input_border};
        --input-text: {input_text};
        --input-placeholder: {input_placeholder};
        --input-focus-border: {input_focus_border};
    }}

    /* Global App Container */
    .stApp {{
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    /* Streamlit Native Header & Top Area Styling (Fix White Bar in Dark Mode) */
    header[data-testid="stHeader"] {{
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
        border-bottom: 1px solid var(--border-color) !important;
    }}

    header[data-testid="stHeader"] svg,
    header[data-testid="stHeader"] button {{
        color: var(--text-primary) !important;
        fill: var(--text-primary) !important;
    }}

    [data-testid="stDecoration"] {{
        display: none !important;
    }}

    .main .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }}

    /* Sidebar High-Contrast Styling */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }}

    /* Sidebar Header Right-Aligned Layout */
    div[data-testid="stSidebarHeader"] {{
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        padding-top: 14px !important;
        padding-bottom: 0px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
        height: auto !important;
    }}

    div[data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
    }}

    div[data-testid="stSidebarCollapseButton"] button {{
        margin-left: auto !important;
        margin-right: 0 !important;
    }}

    /* Modern Hamburger Menu Sidebar Toggle (Replaces Double Chevron ≫) */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"],
    button[data-testid="stExpandSidebarButton"],
    button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"] {{
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        min-height: 44px !important;
        max-width: 44px !important;
        max-height: 44px !important;
        border-radius: 11px !important;
        background-color: {sb_btn_bg} !important;
        background: {sb_btn_bg} !important;
        border: 1px solid {sb_btn_border} !important;
        box-shadow: var(--card-shadow) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        padding: 0 !important;
        visibility: visible !important;
        opacity: 1 !important;
        transition: all 0.15s ease !important;
        z-index: 1000 !important;
    }}

    [data-testid="stExpandSidebarButton"],
    button[data-testid="stExpandSidebarButton"],
    button[aria-label="Expand sidebar"] {{
        margin: 10px 0 0 14px !important;
    }}

    /* Hamburger Button Hover, Focus & Active States */
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stExpandSidebarButton"]:hover,
    button[data-testid="stExpandSidebarButton"]:hover,
    button[aria-label="Expand sidebar"]:hover,
    button[aria-label="Collapse sidebar"]:hover {{
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        border-color: var(--accent-primary) !important;
        box-shadow: 0 2px 8px rgba(109, 40, 217, 0.2) !important;
    }}

    [data-testid="stSidebarCollapseButton"] button:focus,
    [data-testid="stExpandSidebarButton"]:focus,
    button[data-testid="stExpandSidebarButton"]:focus,
    button[aria-label="Expand sidebar"]:focus,
    button[aria-label="Collapse sidebar"]:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px {input_focus_ring} !important;
        outline: none !important;
    }}

    [data-testid="stSidebarCollapseButton"] button:active,
    [data-testid="stExpandSidebarButton"]:active,
    button[data-testid="stExpandSidebarButton"]:active,
    button[aria-label="Expand sidebar"]:active,
    button[aria-label="Collapse sidebar"]:active {{
        transform: scale(0.96) !important;
    }}

    /* Inner Span Centering */
    [data-testid="stSidebarCollapseButton"] button > span,
    [data-testid="stExpandSidebarButton"] > span,
    button[data-testid="stExpandSidebarButton"] > span,
    button[aria-label="Expand sidebar"] > span,
    button[aria-label="Collapse sidebar"] > span {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 100% !important;
    }}

    /* Replace Material Chevron with 3-Line Hamburger SVG Icon */
    [data-testid="stSidebarCollapseButton"] button span[data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"],
    button[data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"],
    button[aria-label="Expand sidebar"] span[data-testid="stIconMaterial"],
    button[aria-label="Collapse sidebar"] span[data-testid="stIconMaterial"] {{
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
        width: 20px !important;
        height: 20px !important;
        display: block !important;
        position: relative !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='3.5' y1='6' x2='20.5' y2='6'/%3E%3Cline x1='3.5' y1='12' x2='20.5' y2='12'/%3E%3Cline x1='3.5' y1='18' x2='20.5' y2='18'/%3E%3C/svg%3E") no-repeat center !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='3.5' y1='6' x2='20.5' y2='6'/%3E%3Cline x1='3.5' y1='12' x2='20.5' y2='12'/%3E%3Cline x1='3.5' y1='18' x2='20.5' y2='18'/%3E%3C/svg%3E") no-repeat center !important;
        -webkit-mask-size: 20px 20px !important;
        mask-size: 20px 20px !important;
        background-color: {sb_btn_icon} !important;
        transition: background-color 0.15s ease !important;
    }}

    /* Change Hamburger Icon color on Button Hover */
    [data-testid="stSidebarCollapseButton"] button:hover span[data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"]:hover span[data-testid="stIconMaterial"],
    button[data-testid="stExpandSidebarButton"]:hover span[data-testid="stIconMaterial"],
    button[aria-label="Expand sidebar"]:hover span[data-testid="stIconMaterial"],
    button[aria-label="Collapse sidebar"]:hover span[data-testid="stIconMaterial"] {{
        background-color: var(--accent-primary) !important;
    }}

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-primary) !important;
    }}

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] textarea {{
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }}

    [data-testid="stSidebar"] svg {{
        fill: var(--text-primary) !important;
        color: var(--text-primary) !important;
    }}

    /* Top Navigation Bar */
    .top-navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1.25rem;
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: var(--card-shadow);
    }}

    .header-branding-section {{
        margin-top: 0;
        margin-bottom: 0.25rem;
    }}

    .brand-title {{
        font-size: 1.55rem;
        font-weight: 700;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0;
        line-height: 1.25;
    }}

    .brand-title span {{
        color: var(--accent-primary);
    }}

    .brand-subtitle {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0.25rem 0 0 0;
        font-weight: 400;
    }}

    /* Popular Shortcuts Horizontal Row */
    .shortcuts-header-label {{
        font-size: 0.75rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
        margin-top: 0.25rem;
    }}

    div[class*="st-key-quick_nav_"] button {{
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
        box-shadow: var(--card-shadow) !important;
    }}

    div[class*="st-key-quick_nav_"] button:hover {{
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        background-color: var(--bg-secondary) !important;
        box-shadow: 0 2px 6px rgba(109, 40, 217, 0.15) !important;
    }}

    /* Fintech Cards */
    .fintech-card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: var(--card-shadow);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 1rem;
    }}

    .fintech-card:hover {{
        border-color: var(--accent-primary);
        box-shadow: var(--card-hover-shadow);
    }}

    /* Metric Cards */
    .metric-tile {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem 1.15rem;
        box-shadow: var(--card-shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}

    .metric-tile:hover {{
        border-color: var(--accent-primary);
    }}

    .metric-tile-label {{
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin-bottom: 0.35rem;
    }}

    .metric-tile-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
    }}

    .metric-tile-subtext {{
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
    }}

    /* Price Hero Box */
    .price-hero {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: var(--card-shadow);
        margin-bottom: 1.25rem;
    }}

    .price-hero-value {{
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.1;
    }}

    /* Badges */
    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }}

    .badge-positive {{
        background-color: {badge_pos_bg};
        color: var(--color-positive);
        border: 1px solid var(--color-positive);
    }}

    .badge-negative {{
        background-color: {badge_neg_bg};
        color: var(--color-negative);
        border: 1px solid var(--color-negative);
    }}

    .badge-warning {{
        background-color: {badge_warn_bg};
        color: var(--color-warning);
        border: 1px solid var(--color-warning);
    }}

    .badge-neutral {{
        background-color: var(--bg-secondary);
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }}

    /* Company Overview Header */
    .company-banner {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--card-shadow);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 1rem;
    }}

    .company-name {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }}

    .company-meta {{
        font-size: 0.85rem;
        color: var(--text-secondary);
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }}

    /* Tabs Styling — Dark & Light Mode Visibility */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: var(--bg-primary) !important;
        border-bottom: 1px solid var(--border-color) !important;
        padding-bottom: 0;
    }}

    .stTabs [data-baseweb="tab"],
    .stTabs [data-testid="stTab"] {{
        background-color: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 0.65rem 1.1rem !important;
        border-radius: 6px 6px 0 0 !important;
        transition: color 0.15s ease, background-color 0.15s ease !important;
    }}

    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-testid="stTab"] p,
    .stTabs [data-testid="stTab"] span,
    .stTabs [data-testid="stTab"] div {{
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }}

    .stTabs [data-baseweb="tab"]:hover,
    .stTabs [data-testid="stTab"]:hover {{
        background-color: {tab_active_bg} !important;
    }}

    .stTabs [data-baseweb="tab"]:hover p,
    .stTabs [data-baseweb="tab"]:hover span,
    .stTabs [data-baseweb="tab"]:hover div,
    .stTabs [data-testid="stTab"]:hover p,
    .stTabs [data-testid="stTab"]:hover span,
    .stTabs [data-testid="stTab"]:hover div {{
        color: var(--text-primary) !important;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs [data-testid="stTab"][aria-selected="true"] {{
        color: var(--accent-primary) !important;
        background-color: {tab_active_bg} !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--accent-primary) !important;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab"][aria-selected="true"] span,
    .stTabs [data-baseweb="tab"][aria-selected="true"] div,
    .stTabs [data-testid="stTab"][aria-selected="true"] p,
    .stTabs [data-testid="stTab"][aria-selected="true"] span,
    .stTabs [data-testid="stTab"][aria-selected="true"] div {{
        color: var(--accent-primary) !important;
        font-weight: 600 !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: var(--accent-primary) !important;
    }}

    .stTabs [data-baseweb="tab-border"] {{
        background-color: var(--border-color) !important;
    }}

    /* High-Contrast Button Styling */
    .stButton button {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        padding: 0.45rem 0.9rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        box-shadow: var(--card-shadow) !important;
        transition: all 0.15s ease !important;
    }}

    .stButton button p,
    .stButton button span {{
        color: var(--text-primary) !important;
    }}

    .stButton button:hover {{
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        background-color: {tab_active_bg} !important;
    }}

    .stButton button:hover p,
    .stButton button:hover span {{
        color: var(--accent-primary) !important;
    }}

    /* Modern Sliding Pill Theme Toggle Switch (Reference Design) */
    div[class*="st-key-theme_pill_toggle"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.85rem !important;
        margin-bottom: 0.75rem !important;
        box-shadow: var(--card-shadow) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    div[class*="st-key-theme_pill_toggle"]:hover {{
        border-color: var(--accent-primary) !important;
        box-shadow: var(--card-hover-shadow) !important;
    }}

    div[class*="st-key-theme_pill_toggle"] label {{
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        cursor: pointer !important;
        gap: 0.75rem !important;
    }}

    div[class*="st-key-theme_pill_toggle"] label p {{
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin: 0 !important;
        letter-spacing: 0.3px !important;
    }}

    /* Toggle Track - Inactive (Light Mode / OFF) */
    div[class*="st-key-theme_pill_toggle"] span:has(input:not(:checked)) + div,
    div[class*="st-key-theme_pill_toggle"] [data-testid="stCheckbox"] > div:first-child,
    div[class*="st-key-theme_pill_toggle"] div[role="switch"] {{
        background-color: #CBD5E1 !important;
        border: 1px solid #94A3B8 !important;
        border-radius: 9999px !important;
        transition: background-color 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s ease !important;
    }}

    /* Toggle Track - Active (Dark Mode / ON) */
    div[class*="st-key-theme_pill_toggle"] span:has(input:checked) + div,
    div[class*="st-key-theme_pill_toggle"] input:checked + div,
    div[class*="st-key-theme_pill_toggle"] div[role="switch"][aria-checked="true"] {{
        background-color: var(--accent-primary) !important;
        border-color: var(--accent-primary) !important;
    }}

    /* Sliding Circular Knob */
    div[class*="st-key-theme_pill_toggle"] span:has(input) + div > div,
    div[class*="st-key-theme_pill_toggle"] div[role="switch"] > div,
    div[class*="st-key-theme_pill_toggle"] [data-testid="stCheckbox"] > div:first-child > div {{
        background-color: #FFFFFF !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s ease !important;
    }}

    /* Watchlist Buttons Vertical Center Alignment & Uniform Proportions */
    div[class*="st-key-wl_select_"] button,
    div[class*="st-key-wl_remove_"] button {{
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }}

    div[class*="st-key-wl_remove_"] button {{
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        line-height: 1 !important;
        padding: 0 !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }}

    div[class*="st-key-wl_remove_"] button p,
    div[class*="st-key-wl_remove_"] button span {{
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[class*="st-key-wl_remove_"] button:hover {{
        background-color: rgba(244, 63, 94, 0.15) !important;
        border-color: var(--color-negative) !important;
        color: var(--color-negative) !important;
    }}

    div[class*="st-key-wl_remove_"] button:hover p,
    div[class*="st-key-wl_remove_"] button:hover span {{
        color: var(--color-negative) !important;
    }}

    /* Equal-Height KPI Cards Grid */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 0.65rem;
        margin-bottom: 1.25rem;
        width: 100%;
    }}

    @media (min-width: 1024px) {{
        .kpi-grid {{
            grid-template-columns: repeat(7, 1fr);
        }}
    }}

    .kpi-card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.85rem 0.9rem;
        box-shadow: var(--card-shadow);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 125px;
        height: 100%;
        box-sizing: border-box;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}

    .kpi-card:hover {{
        border-color: var(--accent-primary);
        box-shadow: var(--card-hover-shadow);
    }}

    .kpi-card-label {{
        font-size: 0.73rem;
        font-weight: 600;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        color: var(--text-secondary);
        min-height: 2.2rem;
        display: flex;
        align-items: flex-start;
        line-height: 1.25;
        overflow: hidden;
    }}

    .kpi-card-value {{
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
        margin: 0.25rem 0;
    }}

    .kpi-card-footer {{
        margin-top: auto;
        display: flex;
        align-items: center;
    }}

    /* Redesigned Current Holdings Section & Table */
    .holdings-toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
        gap: 1rem;
        flex-wrap: wrap;
    }}

    .holdings-table-container {{
        width: 100%;
        overflow-x: auto;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background-color: var(--bg-card);
        box-shadow: var(--card-shadow);
        margin-bottom: 1.5rem;
    }}

    .fintech-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
        text-align: left;
    }}

    .fintech-table th {{
        background-color: var(--bg-secondary);
        color: var(--text-secondary);
        font-weight: 600;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border-color);
        white-space: nowrap;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .fintech-table td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border-color);
        color: var(--text-primary);
        white-space: nowrap;
        vertical-align: middle;
    }}

    .fintech-table tr:last-child td {{
        border-bottom: none;
    }}

    .fintech-table tr:hover td {{
        background-color: rgba(109, 40, 217, 0.04);
    }}

    /* Download Button & Form Submit Buttons */
    .stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button,
    button[kind="formSubmit"] {{
        background-color: var(--accent-primary) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        box-shadow: var(--card-shadow) !important;
        transition: opacity 0.15s ease !important;
    }}

    .stDownloadButton > button p,
    .stDownloadButton > button span,
    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span {{
        color: #FFFFFF !important;
    }}

    .stDownloadButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    button[kind="formSubmit"]:hover {{
        opacity: 0.9 !important;
        color: #FFFFFF !important;
    }}

    /* Form & Input Labels (Light & Dark Theme Visibility) */
    label,
    label p,
    label span,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stWidgetLabel"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stNumberInput"] label p,
    div[data-testid="stDateInput"] label,
    div[data-testid="stDateInput"] label p,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stTextArea"] label,
    div[data-testid="stTextArea"] label p,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label span {{
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        opacity: 1 !important;
    }}

    /* Text Inputs, Number Inputs, Date Pickers, Textareas */
    div[data-testid="stTextInput"] > div > div, 
    div[data-testid="stDateInput"] > div > div,
    div[data-testid="stNumberInput"] > div > div,
    div[data-testid="stTextArea"] > div > div,
    .stTextInput > div > div, 
    .stDateInput > div > div,
    .stNumberInput > div > div,
    .stTextArea > div > div {{
        background-color: var(--input-bg) !important;
        background: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 6px !important;
    }}

    div[data-testid="stTextInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    .stTextInput input,
    .stDateInput input,
    .stNumberInput input,
    .stTextArea textarea {{
        background-color: transparent !important;
        background: transparent !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        font-size: 0.875rem !important;
        color-scheme: {'dark' if is_dark else 'light'} !important;
    }}

    div[data-testid="stDateInput"] input[type="date"] {{
        background-color: transparent !important;
        background: transparent !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        color-scheme: {'dark' if is_dark else 'light'} !important;
    }}

    input::placeholder,
    textarea::placeholder {{
        color: var(--input-placeholder) !important;
        -webkit-text-fill-color: var(--input-placeholder) !important;
        opacity: 0.85 !important;
    }}

    div[data-testid="stTextInput"] > div > div:focus-within, 
    div[data-testid="stDateInput"] > div > div:focus-within,
    div[data-testid="stNumberInput"] > div > div:focus-within,
    div[data-testid="stTextArea"] > div > div:focus-within,
    .stTextInput > div > div:focus-within, 
    .stDateInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within,
    .stTextArea > div > div:focus-within {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px {input_focus_ring} !important;
    }}

    /* Number Input Increment/Decrement Buttons */
    div[data-testid="stNumberInput"] button,
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"] {{
        background-color: transparent !important;
        color: var(--input-text) !important;
        border: none !important;
    }}

    div[data-testid="stNumberInput"] button svg,
    div[data-testid="stNumberInput"] svg {{
        fill: var(--input-text) !important;
        color: var(--input-text) !important;
        opacity: 0.85 !important;
    }}

    div[data-testid="stNumberInput"] button:hover svg {{
        fill: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        opacity: 1 !important;
    }}

    /* Date Input & React-Aria Date Input Fields */
    [data-testid="stDateInputField"],
    .react-aria-DateField,
    [data-testid="stDateInputField"] div {{
        background-color: transparent !important;
        background: transparent !important;
    }}

    [data-testid="stDateInputField"] span,
    .react-aria-DateField span {{
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}

    button[data-testid="stDateInputCalendarButton"] {{
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
    }}

    button[data-testid="stDateInputCalendarButton"] svg,
    div[data-testid="stDateInput"] svg,
    .stDateInput svg {{
        fill: var(--input-text) !important;
        color: var(--input-text) !important;
        opacity: 0.85 !important;
    }}

    button[data-testid="stDateInputCalendarButton"]:hover svg {{
        fill: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}

    /* Selectboxes & Dropdowns — React-Aria & BaseWeb Full Contrast */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] .react-aria-ComboBox > div {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
    }}

    [data-testid="stSelectbox"] input,
    [data-testid="stSelectbox"] input[role="combobox"],
    .react-aria-ComboBox input,
    [data-testid="stSelectbox"] div[data-baseweb="select"] div,
    [data-testid="stSelectbox"] div[data-baseweb="select"] span {{
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}

    [data-testid="stSelectbox"] input::placeholder {{
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        opacity: 0.75 !important;
    }}

    [data-testid="stSelectbox"] svg,
    [data-testid="stSelectbox"] button svg {{
        fill: var(--text-primary) !important;
        color: var(--text-primary) !important;
    }}

    div[role="listbox"],
    ul[role="listbox"],
    [data-baseweb="popover"],
    [data-testid="stSelectbox"] [role="listbox"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        box-shadow: var(--card-hover-shadow) !important;
    }}

    div[role="listbox"] [role="option"],
    ul[role="listbox"] li,
    [role="option"] {{
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 0.75rem !important;
        transition: background-color 0.15s ease, color 0.15s ease !important;
    }}

    div[role="listbox"] [role="option"]:hover,
    div[role="listbox"] [role="option"][data-focused="true"],
    div[role="listbox"] [role="option"][aria-selected="true"],
    ul[role="listbox"] li:hover {{
        background-color: var(--bg-secondary) !important;
        color: var(--accent-primary) !important;
    }}

    /* Radio buttons & Checkboxes */
    .stRadio label,
    .stRadio label p,
    .stRadio label span,
    div[data-testid="stRadioGroup"] label,
    div[data-testid="stRadioGroup"] p,
    div[data-testid="stRadioGroup"] span,
    [data-testid="stRadioOption"] p,
    [data-testid="stRadioOption"] span,
    .stCheckbox label,
    .stCheckbox label p,
    .stCheckbox label span {{
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}

    /* Unselected radio indicator circle (Eliminates White Radio Circle in Dark Mode) */
    [data-testid="stRadioOption"]:not([data-selected="true"]) > div > div:first-child,
    [data-testid="stRadioOption"]:not([data-selected="true"]) [class*="ex50key4"] {{
        background-color: var(--input-bg) !important;
        background: var(--input-bg) !important;
        border: 2px solid var(--border-color) !important;
    }}

    [data-testid="stRadioOption"]:not([data-selected="true"]) > div > div:first-child > div,
    [data-testid="stRadioOption"]:not([data-selected="true"]) [class*="ex50key5"] {{
        background-color: transparent !important;
        background: transparent !important;
        display: none !important;
    }}

    /* Selected radio indicator circle */
    [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child,
    [data-testid="stRadioOption"][data-selected="true"] [class*="ex50key4"] {{
        background-color: var(--accent-primary) !important;
        background: var(--accent-primary) !important;
        border: 2px solid var(--accent-primary) !important;
    }}

    [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div,
    [data-testid="stRadioOption"][data-selected="true"] [class*="ex50key5"] {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        display: block !important;
    }}

    /* Expanders & Collapsible Form Cards (Eliminates White Header Strip) */
    [data-testid="stExpander"],
    [data-testid="stExpander"] details {{
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }}

    [data-testid="stExpander"] details summary {{
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1rem !important;
        border: none !important;
        border-bottom: 1px solid var(--border-color) !important;
        transition: background-color 0.15s ease, color 0.15s ease !important;
    }}

    [data-testid="stExpander"] details:not([open]) summary {{
        border-bottom: none !important;
    }}

    [data-testid="stExpander"] details summary:hover {{
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
    }}

    [data-testid="stExpander"] details summary *,
    [data-testid="stExpander"] details summary div,
    [data-testid="stExpander"] details summary span {{
        background-color: transparent !important;
        background: transparent !important;
    }}

    [data-testid="stExpander"] details summary p,
    [data-testid="stExpander"] details summary span {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    [data-testid="stExpander"] details summary:hover p,
    [data-testid="stExpander"] details summary:hover span {{
        color: var(--accent-primary) !important;
    }}

    [data-testid="stExpander"] details summary svg {{
        fill: var(--text-primary) !important;
        color: var(--text-primary) !important;
        transition: fill 0.15s ease, color 0.15s ease !important;
    }}

    [data-testid="stExpander"] details summary:hover svg {{
        fill: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}

    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: none !important;
        padding: 1.25rem 1rem !important;
    }}

    /* Tables & DataFrames */
    .stDataFrame {{
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background-color: var(--bg-card);
        color: var(--text-primary) !important;
    }}

    [data-testid="stDataFrame"] div {{
        color: var(--text-primary) !important;
    }}

    /* Dataframe Toolbar Controls & Icons */
    [data-testid="stElementToolbar"] {{
        opacity: 1 !important;
    }}

    [data-testid="stElementToolbarButtonContainer"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 3px 4px !important;
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
    }}

    button[data-testid="stBaseButton-elementToolbar"],
    [data-testid="stElementToolbarButton"] button {{
        background-color: transparent !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 5px 6px !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: background-color 0.15s ease, color 0.15s ease !important;
    }}

    button[data-testid="stBaseButton-elementToolbar"]:hover,
    [data-testid="stElementToolbarButton"] button:hover {{
        background-color: rgba(99, 102, 241, 0.2) !important;
        color: var(--accent-primary) !important;
    }}

    button[data-testid="stBaseButton-elementToolbar"]:focus-visible,
    [data-testid="stElementToolbarButton"] button:focus-visible {{
        outline: 2px solid var(--accent-primary) !important;
        outline-offset: 1px !important;
    }}

    button[data-testid="stBaseButton-elementToolbar"] svg,
    [data-testid="stElementToolbarButtonIcon"],
    [data-testid="stElementToolbarButton"] svg {{
        color: var(--text-primary) !important;
        fill: var(--text-primary) !important;
        stroke: var(--text-primary) !important;
        width: 17px !important;
        height: 17px !important;
        transition: color 0.15s ease, fill 0.15s ease !important;
    }}

    button[data-testid="stBaseButton-elementToolbar"]:hover svg,
    [data-testid="stElementToolbarButton"] button:hover svg {{
        color: var(--accent-primary) !important;
        fill: var(--accent-primary) !important;
        stroke: var(--accent-primary) !important;
    }}

    /* Dataframe Column Visibility Menu & Checkbox Styling */
    [data-testid="stDataFrameColumnVisibilityMenu"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45) !important;
        color: var(--text-primary) !important;
        padding: 0.85rem !important;
        min-width: 180px !important;
    }}

    [data-testid="stDataFrameColumnVisibilityMenu"] label,
    [data-testid="stDataFrameColumnVisibilityMenu"] span,
    [data-testid="stDataFrameColumnVisibilityMenu"] p,
    [data-testid="stDataFrameColumnVisibilityMenu"] div {{
        color: var(--text-primary) !important;
        font-size: 0.85rem !important;
    }}

    [data-testid="stDataFrameColumnVisibilityMenu"] label:hover {{
        background-color: rgba(99, 102, 241, 0.12) !important;
        border-radius: 4px !important;
    }}

    [data-testid="stDataFrameColumnVisibilityMenu"] input[type="checkbox"] {{
        accent-color: var(--accent-primary) !important;
    }}

    /* Tooltips across Dataframes and Controls */
    [data-testid="stTooltipContent"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        box-shadow: var(--card-shadow) !important;
        font-size: 0.78rem !important;
    }}

    /* Portfolio Selector & Popover Management Button */
    div[data-testid="stPopover"] button,
    div[data-testid="stPopover"] button[kind="secondary"],
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"],
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] .stBaseButton-secondary {{
        height: 42px !important;
        min-height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        border-radius: 6px !important;
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        box-shadow: var(--card-shadow) !important;
        transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease !important;
        padding: 0.5rem 1rem !important;
    }}

    div[data-testid="stPopover"] button p,
    div[data-testid="stPopover"] button span,
    div[data-testid="stPopover"] button div {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stPopover"] button:hover,
    div[data-testid="stPopover"] button[kind="secondary"]:hover,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"]:hover,
    div[data-testid="stPopover"] > button:hover {{
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
    }}

    div[data-testid="stPopover"] button:hover p,
    div[data-testid="stPopover"] button:hover span,
    div[data-testid="stPopover"] button:hover div {{
        color: var(--accent-primary) !important;
    }}

    div[data-testid="stPopover"] button:focus,
    div[data-testid="stPopover"] button[kind="secondary"]:focus,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"]:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px {input_focus_ring} !important;
        outline: none !important;
    }}

    div[data-testid="stPopover"] button svg,
    div[data-testid="stPopover"] button span svg,
    div[data-testid="stPopover"] button div svg {{
        fill: var(--text-primary) !important;
        color: var(--text-primary) !important;
        margin-left: 0.35rem !important;
    }}

    div[data-testid="stPopover"] button:hover svg,
    div[data-testid="stPopover"] button:hover span svg,
    div[data-testid="stPopover"] button:hover div svg {{
        fill: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}

    /* Save Transaction to Ledger Button (Vibrant Purple Accent) */
    div[class*="st-key-btn_save_tx"] button {{
        background-color: var(--accent-primary) !important;
        background: var(--accent-primary) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        padding: 0.55rem 1rem !important;
    }}

    div[class*="st-key-btn_save_tx"] button p,
    div[class*="st-key-btn_save_tx"] button span {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    div[class*="st-key-btn_save_tx"] button:hover {{
        background-color: var(--accent-secondary) !important;
        background: var(--accent-secondary) !important;
        border-color: var(--accent-secondary) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25) !important;
        opacity: 0.95 !important;
    }}

    div[class*="st-key-btn_save_tx"] button:focus {{
        box-shadow: 0 0 0 3px {input_focus_ring} !important;
        outline: none !important;
    }}

    div[data-testid="stPopoverBody"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45) !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
    }}

    div[class*="st-key-portfolio_active_select"] [role="combobox"] {{
        height: 42px !important;
        min-height: 42px !important;
    }}

    /* Section Headers */
    .section-title {{
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 1.25rem 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Ticker Shortcut Chips */
    .chip-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.4rem;
    }}

    /* Footer */
    .footer-bar {{
        border-top: 1px solid var(--border-color);
        margin-top: 2.5rem;
        padding: 1.25rem 0;
        text-align: center;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }}
</style>
"""


def render_theme_persistence_script(current_theme: str) -> str:
    """Generate HTML/JavaScript to synchronize active theme with browser localStorage."""
    return f"""
    <script>
        (function() {{
            const activeTheme = "{current_theme}";
            try {{
                const storedTheme = localStorage.getItem("stock_visualizer_theme");
                if (!storedTheme) {{
                    localStorage.setItem("stock_visualizer_theme", activeTheme);
                }} else if (storedTheme !== activeTheme) {{
                    // Update stored theme to match active state
                    localStorage.setItem("stock_visualizer_theme", activeTheme);
                }}
            }} catch (e) {{
                console.error("Theme persistence error:", e);
            }}
        }})();
    </script>
    """


def render_tab_switch_script(tab_index: int, nonce: float = 0.0) -> str:
    """Generate JavaScript to switch Streamlit active tab with nonce to force re-execution."""
    return f"""
    <!-- switch_nonce: {nonce} -->
    <script>
        (function() {{
            let attempts = 0;
            const maxAttempts = 30;
            function switchToTab() {{
                try {{
                    const parentDoc = window.parent.document;
                    const tabs = parentDoc.querySelectorAll('[data-testid="stTab"]');
                    if (tabs && tabs.length > {tab_index}) {{
                        tabs[{tab_index}].click();
                        return;
                    }}
                }} catch (e) {{
                    console.error("Tab switch error:", e);
                }}
                if (attempts < maxAttempts) {{
                    attempts++;
                    setTimeout(switchToTab, 50);
                }}
            }}
            switchToTab();
        }})();
    </script>
    """
