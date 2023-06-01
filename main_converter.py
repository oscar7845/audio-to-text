import flet as ft
import io, os, yaml

def main(page: ft.Page):  

    PEAK_POW = 5000
    AUDIO_SAMPLING_FREQ = 16000
    FPB = 1024
    LARGEST_SHORT_INT16 = 32767 

    # Setting up the window appearence  
    page.title = "Audio to Text App"
    page.window_min_width = 840.0
    page.window_min_height = 480.0
    page.window_width = page.window_width if page.window_width is not None else page.window_min_width
    page.window_height = page.window_height if page.window_height is not None else 820.0

    # on change
    def keep_window_above_method(_):
       page.window_always_on_top = keep_above_box.value
       page.update()

    keep_above_box = ft.Checkbox(label="Keep Above", value=params.get('keep_above', False), on_change=keep_window_above_method)

    def keep_window_above_method():
        pass

    def night_theme_method():
        page.update()
    

    def font_size_method():
        pass

    # Save all the params
    params = {
        'window_width': page.window_width,
        'window_height': page.window_height
    }

    model_dropdown = ft.Dropdown(
            options=[
            ],
            label="Speech To Text Model",
            expand=True,
        )
    
    settings_controls = ft.Column(
    [
        ft.Container(
            content=ft.Row(
                [
                    model_dropdown,                
                ],
            ),
        ),
    ],
    visible=True
)

    page.add(
        settings_controls,
        keep_above_box
        #
    )


if __name__ == "__main__":
    ft.app(target=main)