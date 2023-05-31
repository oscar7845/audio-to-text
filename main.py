import flet as ft

def main(page: ft.Page):  

    # Setting up the window appearence  
    page.title = "Audio to Text App"
    page.window_min_width = 840.0
    page.window_min_height = 480.0
    page.window_width = page.window_width if page.window_width is not None else page.window_min_width
    page.window_height = page.window_height if page.window_height is not None else 820.0

    # on change
    def text_background_method():
        page.update()

    def keep_window_above_method():
        pass

    def night_theme_method():
        page.update()
    

    def font_size_method():
        pass



if __name__ == "__main__":
    ft.app(target=main)