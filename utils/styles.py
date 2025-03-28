# utils/styles.py
def style_calendar(status):
    color_map = {
        "P": "background-color: #8AE29C; color: black;",
        "A": "background-color: #FF9B9B; color: black;",
        "MIS": "background-color: #FFEB99; color: black;",
        "LA": "background-color: #FFAA66; color: black;"
    }
    return color_map.get(status, "")