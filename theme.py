COLORS = {
    'oxford_blue': '#0b132b',      # main background
    'space_cadet': '#1c2541',     # secondary background
    'yinmn_blue': '#3a506b',      # frames, etc
    'verdigris': '#5bc0be',       # buttons
    'fluorescent_cyan': '#6fffe9'  # button text, highlights
}

FONT_SIZES = {
    'title': ("Arial", 20, "bold"),
    'header': ("Arial", 14, "bold"),
    'body': ("Arial", 12),
    'italic': ("Arial", 11, "italic")
}

ENTRY_STYLE = {
    'font': ("Arial", 14),
    'bg': COLORS['yinmn_blue'],
    'fg': COLORS['fluorescent_cyan'],
    'insertbackground': COLORS['verdigris'],
    'relief': 'flat',
    'bd': 2
}

BUTTON_STYLE = {
    'bg': COLORS['verdigris'],
    'fg': COLORS['oxford_blue'],
    'font': ("Arial", 12, "bold"),
    'relief': 'flat',
    'padx': 25,
    'pady': 12,
    'activebackground': COLORS['fluorescent_cyan'],
    'activeforeground': COLORS['oxford_blue'],
    'cursor': 'hand2'
}

SCROLLBAR_STYLE = {
    "background": COLORS['yinmn_blue'],
    "troughcolor": COLORS['space_cadet'],
    "bordercolor": COLORS['yinmn_blue'],
    "arrowcolor": COLORS['fluorescent_cyan'],
    "darkcolor": COLORS['yinmn_blue'],
    "lightcolor": COLORS['verdigris']
}
