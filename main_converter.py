import flet as ft
import io, os, yaml
import pyaudio

def main(page: ft.Page):  
    PEAK_POW = 5000
    AUDIO_SAMPLING_FREQ = 16000
    FPB = 1024
    LARGEST_SHORT_INT16 = 32767 

    # Setting up the window appearence  
    page.title = "Audio to Text App"
    page.window_min_width = 750.0
    page.window_min_height = 475.0
    page.window_width = page.window_width if page.window_width is not None else page.window_min_width
    page.window_height = page.window_height if page.window_height is not None else 820.0

    # on change
    def keep_window_above_method(_):
       page.window_always_on_top = keep_above_box.value
       page.update()

    keep_above_box = ft.Checkbox(on_change=keep_window_above_method)

    def text_background_method(_):
        for list_item in convertion_lst.controls:
            if text_bg_box.value:
                list_item.bgcolor = ft.colors.BLACK if nightmode_box.value else ft.colors.WHITE
            else:
                list_item.bgcolor = None
        convertion_lst.update()

    text_bg_box = ft.Checkbox(on_change=text_background_method)
    nightmode_box = ft.Checkbox()
    convertion_lst = ft.ListView()


    def night_theme_method():
        page.theme_mode = ft.ThemeMode.DARK if nightmode_box.value else ft.ThemeMode.LIGHT
        text_background_method()
        page.update()
    night_theme_method(None)
    

    def font_size_method():
        for list_item in convertion_lst.controls:
            list_item.size = int(text_size_selector.value)
        convertion_lst.update()

    text_size_selector = ft.Dropdown()

    def translate_language_method():
        pass

    lang_selector = ft.Dropdown(
        on_change=translate_language_method
    )
    translate_lang_box = ft.Checkbox(disabled=lang_selector.value == 'en')
    translate_lang_box.disabled = True # otherwise default on

    ##
    # User Interface
    ##

    # Save all the params
    params = {
        'window_width': page.window_width,
        'window_height': page.window_height
    }

    model_selector = ft.Dropdown(
        options=[
            ft.dropdown.Option('tiny', text="Smallest"),
            ft.dropdown.Option('base', text="Default"),
            ft.dropdown.Option('small', text="Small"),
            ft.dropdown.Option('medium', text="Medium"),
            ft.dropdown.Option('large', text="Large"),
        ],
        label="Selected Audio/Speech to Text Type",
        expand=True,
        text_size=15,
    )

    mics = {}
    paudio = pyaudio.PyAudio()
    for i in range(paudio.get_device_count()):
        device_details = paudio.get_device_info_by_index(i)
        if device_details['maxInputChannels'] > 0 and device_details['hostApi'] == 0:
            mics[device_details['index']] = device_details['name']

    default_microphone = paudio.get_default_input_device_info()['index']
    selected_microphone = int(params.get('microphone_index', default_microphone))
    if selected_microphone not in mics:
        selected_microphone = default_microphone

    mic_selector = ft.Dropdown(
        options=[ft.dropdown.Option(index, text=mic) for index, mic in mics.items()],
        label="Selected Audio Input Device",
        expand=True,
        content_padding=ft.padding.only(top=5, bottom=5, left=10),
        text_size=15,
    )

    params_config = ft.Column(
    [
        ft.Container(
            content=ft.Row(
                [
                    model_selector,
                ],
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
        ),
        ft.Container(
            content=ft.Row(
                [
                    mic_selector,
                ],
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
        ),

        ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            lang_selector,
                            text_size_selector,
                        ]
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
        ),
    ],
    visible=True
    )

    #--#

    page.add(
        params_config,
        ft.Container(
            content=convertion_lst,
        ),
    )


if __name__ == "__main__":
    ft.app(target=main)