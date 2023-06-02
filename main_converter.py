import io
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
from time import sleep

import audioop
import flet as ft
import numpy
import pyaudio
import torch
import wave
import whisper
import yaml
from whisper.tokenizer import LANGUAGES

from constants import app_params, params
from constants import AUDIO_SAMPLING_FREQ, FPB, LARGEST_SHORT_INT16

def main(page: ft.page):
    # Setting up the window appearence
    page.title = "Audio to Text App"
    page.window_min_width = 700.0
    page.window_width = 700.0
    page.window_min_height = 475.0
    page.window_height = params.get('window_height', 820.0)
    PEAK_POW = 5000

    #---------------------#
    # On change functions #
    #---------------------#

    def keep_window_above_method(_):
       page.window_always_on_top = keep_above_box.value
       page.update()

    def text_background_method(_):
        for list_item in convertion_lst.controls:
            if text_bg_box.value:
                list_item.bgcolor = ft.colors.BLACK if nightmode_box.value else ft.colors.WHITE
            else:
                list_item.bgcolor = None
        convertion_lst.update()

    def night_theme_method(_):
        page.theme_mode = ft.ThemeMode.DARK if nightmode_box.value else ft.ThemeMode.LIGHT
        text_background_method(_)
        page.update()

    def translate_language_method(_):
        translate_lang_box.disabled = translate_lang_box.value = False if lang_selector.value == 'en' else translate_lang_box.disabled
        translate_lang_box.update()

    def font_size_method(_):
        for list_item in convertion_lst.controls:
            list_item.size = int(text_size_selector.value)
        convertion_lst.update()

    audio_type:whisper.Whisper = None
    selected_audio_type:str = None
    is_active_transcriber = False
    end_capture:function = None
    data_collection_thread:Thread = None
    myqueue = Queue()
    
    def speech_processor_method(_):
        nonlocal audio_type, selected_audio_type, is_active_transcriber, end_capture, data_collection_thread, start_recording_thread
        page.splash = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center
        )
        page.update()   

        if not is_active_transcriber:
            mytype = model_selector.value
            if mytype != "large" and lang_selector.value == 'en':
                mytype = mytype + ".en"

            # Reload the audio type only if got changed
            if not audio_type or not selected_audio_type:
                device = "cuda" if torch.has_cuda else 'cpu'
                audio_type = whisper.load_model(mytype, device)
                selected_audio_type = mytype
            elif audio_type and selected_audio_type and selected_audio_type != mytype:
                device = "cuda" if torch.has_cuda else 'cpu'
                audio_type = whisper.load_model(mytype, device)
                selected_audio_type = mytype

            type_index = int(mic_selector.value)
            if not data_collection_thread:
                mystream = paudio.open(format=pyaudio.paInt16,
                                       channels=1,
                                       rate=AUDIO_SAMPLING_FREQ,
                                       input=True,
                                       frames_per_buffer=FPB,
                                       input_device_index=type_index)
                data_collection_thread = Thread(target=recording_thread_method, args=[mystream])
                start_recording_thread = True
                data_collection_thread.start()

            convertion_text.value = "Stop Transcribing"
            convertion_icon.name = "end_transcriber"
            convertion_button.bgcolor = ft.colors.DEEP_ORANGE_400

            # Turn off all of the controls
            model_selector.disabled = True
            mic_selector.disabled = True
            lang_selector.disabled = True
            translate_lang_box.disabled = True
            params_config.visible = False

            # Make ui see-trough
            if transparent_box.value:
                page.window_bgcolor = ft.colors.TRANSPARENT
                page.bgcolor = ft.colors.TRANSPARENT
                page.window_title_bar_hidden = True
                page.window_frameless = True
                draggable_zone1.visible = True
                draggable_zone2.visible = True

            # Save all the params
            params = {
                'speech_model': model_selector.value,
                'translate': translate_lang_box.value,
                'window_width': page.window_width,
                'window_height': page.window_height,
                'microphone_index': mic_selector.value,
                'language': lang_selector.value,
                'text_size': text_size_selector.value,
                'keep_above': keep_above_box.value,
                'night_mode': nightmode_box.value,
                'text_background': text_bg_box.value,
                'transparent': transparent_box.value,
                'volume_threshold': power_slider.value,
                'transcribe_rate': convert_frequency_seconds,
                'upper_limit_record_time': upper_limit_record_time,
                'seconds_of_silence_between_lines': quiet_time,
            }

            with open(app_params, 'w+') as f:
                yaml.dump(params, f)

            is_active_transcriber = True
        else:
            convertion_text.value = "Start Receiving Audio"
            convertion_icon.name = "play_arrow_rounded"
            convertion_button.bgcolor = ft.colors.TEAL_400
            sound_level_bar.value = 0.01

            # Interrupt record thread
            try:
                if data_collection_thread:
                    start_recording_thread = False
                    data_collection_thread.join()
                    data_collection_thread = None
            except RuntimeError as e:
                print(f"Error while interrupting the data collection thread: {e}")

            # Save the final sample while draining the rest of the data so that we run main loop again. 
            # This so that we create a new line instead of editing last line when starting the transcriber again
            content_data = None
            while not myqueue.empty():
                content_data = myqueue.get()
            if content_data:
                myqueue.put(content_data)

            # Initiliaze controls by enabling them
            model_selector.disabled = False
            mic_selector.disabled = False
            lang_selector.disabled = False
            translate_lang_box.disabled = lang_selector.value == 'en'
            params_config.visible = True

            # Customize here page appearance 
            page.window_bgcolor = None
            page.bgcolor = None
            page.window_title_bar_hidden = False
            page.window_frameless = False
            draggable_zone1.visible = False
            draggable_zone2.visible = False

            # Contain content transcribed and set is active to false
            text_file = "content.txt"
            with open(text_file, 'w+', encoding='utf-8') as f:
                f.writelines('\n'.join([item.value for item in convertion_lst.controls]))

            is_active_transcriber = False

        page.splash = None
        page.update()

    #-----------#
    # UI config #
    #-----------#

    model_selector = ft.Dropdown(
        options=[
            ft.dropdown.Option('tiny', text="Very small (Fastest, low quality)"),
            ft.dropdown.Option('base', text="Default"),
            ft.dropdown.Option('small', text="Small"),
            ft.dropdown.Option('medium', text="Medium"),
            ft.dropdown.Option('large', text="Large (Slowest, high quality)"),
        ],
        label="Selected Audio/Speech to Text Type",
        value=params.get('speech_model', 'base'),
        expand=True,
        content_padding=ft.padding.only(top=5, bottom=5, left=10),
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
        value=selected_microphone,
        expand=True,
        content_padding=ft.padding.only(top=5, bottom=5, left=10),
        text_size=15,
    )

    lang_options = [ft.dropdown.Option("Auto")]
    lang_options += [ft.dropdown.Option(abbr, text=lang.capitalize()) for abbr, lang in LANGUAGES.items()]
    lang_selector = ft.Dropdown(
        options=lang_options,
        label="Selected Language",
        value=params.get('language', "Auto"),
        content_padding=ft.padding.only(top=5, bottom=5, left=10),
        text_size=15,
        on_change=translate_language_method
    )

    text_size_selector = ft.Dropdown(
        options=[ft.dropdown.Option(size) for size in range(8, 66, 2)],
        label="Selected Text Size",
        value=params.get('text_size', 24),
        on_change=font_size_method,
        content_padding=ft.padding.only(top=5, bottom=5, left=10),
        text_size=15,
    )

    translate_lang_box = ft.Checkbox(label="Translate To English", value=params.get('translate', False), disabled=lang_selector.value == 'en')
    nightmode_box = ft.Checkbox(label="Night Mode", value=params.get('night_mode', False), on_change=night_theme_method)
    text_bg_box = ft.Checkbox(label="Text Background", value=params.get('text_background', False), on_change=text_background_method)
    keep_above_box = ft.Checkbox(label="Keep Above", value=params.get('keep_above', False), on_change=keep_window_above_method)
    transparent_box = ft.Checkbox(label="Transparent", value=params.get('transparent', False))

    power_slider = ft.Slider(min=0, max=PEAK_POW, value=params.get('volume_threshold', 300), expand=True, height=20)
    sound_level_bar = ft.ProgressBar(value=0.01, color=ft.colors.DEEP_ORANGE_400)

    convertion_lst = ft.ListView([], spacing=10, padding=20, expand=True, auto_scroll=True)

    convertion_text = ft.Text("Start Receiving Audio")
    convertion_icon = ft.Icon("play_arrow_rounded")

    convertion_button = ft.ElevatedButton(
        content=ft.Row(
            [
                convertion_icon,
                convertion_text
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
        ),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        bgcolor=ft.colors.TEAL_400, color=ft.colors.WHITE,
        on_click=speech_processor_method,
    )

    params_config = ft.Column(
    [
        ft.Container(
            content=ft.Row(
                [
                    model_selector,
                    ft.Icon("help_outline", tooltip="Select type for speech transcription.\nTypes are downloaded the first time they are used.\n It could take time for heavy ones."),
                
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
        ),
        ft.Container(
            content=ft.Row(
                [
                    mic_selector,
                    ft.Icon("help_outline", tooltip="This is the audio input device. \nAudio from this device will be taken as input."),
                ],
                spacing=10,
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
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            translate_lang_box,
                            transparent_box,
                            keep_above_box,
                            text_bg_box,
                            nightmode_box,
                        ]
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=5, vertical=10),
        ),
        ft.Container(
            content=ft.Row(
                [
                    power_slider,
                    ft.Icon("help_outline", tooltip="Volume required to start decoding audio.\nMax volume auto adjusts.")
                ],
                expand=True,
            ),
            padding=ft.padding.only(left=0, right=15, top=0),
        ),
    ],
    visible=True
    )


    draggable_zone1 = ft.Row(
        [
            ft.WindowDragArea(ft.Container(height=30), expand=True),
        ],
        visible=False
    )
    draggable_zone2 = ft.Row(
        [
            ft.WindowDragArea(ft.Container(height=30), expand=True),
        ],
        visible=False
    )

    page.add(
        params_config,
        draggable_zone1,
        ft.Container(
            content=convertion_button,
            padding=ft.padding.only(left=10, right=45, top=5)
        ),
        ft.Container(
            content=sound_level_bar,
            padding=ft.padding.only(left=10, right=45, top=0)
        ),
        draggable_zone2,
        ft.Container(
            content=convertion_lst,
            padding=ft.padding.only(left=15, right=45, top=5),
            expand=True,
        ),
    )

    # set params that could not have been loaded
    night_theme_method(None)
    keep_window_above_method(None)
    text_background_method(None)

    #------------------#
    # Audio processing #
    #------------------#

    start_recording_thread = True

    def recording_thread_method(mystream:pyaudio.Stream):
        nonlocal PEAK_POW
        sample_size = paudio.get_sample_size(pyaudio.paInt16)
        deep_orange = ft.colors.DEEP_ORANGE_400
        teal = ft.colors.TEAL_400
        
        while start_recording_thread:
            # We record very fast in order to update volume bar as fast as possible
            content_data = mystream.read(FPB)
            power = audioop.rms(content_data, sample_size)
            
            if power > PEAK_POW:
                PEAK_POW = power
                power_slider.max = PEAK_POW
                power_slider.update()
            
            sound_level_bar.value = min(power / PEAK_POW, 1.0)
            sound_level_bar.color = deep_orange if power < power_slider.value else teal
            myqueue.put(content_data)
            sound_level_bar.update()


    next_convert_instance = None
    convert_frequency_seconds = float(params.get('transcribe_rate', 0.5))
    convert_frequency = timedelta(seconds=convert_frequency_seconds)
    upper_limit_record_time = params.get('upper_limit_record_time', 30)
    quiet_time = params.get('seconds_of_silence_between_lines', 0.5)
    last_sample = bytes()
    quiet_samples = 0
    sample_size = paudio.get_sample_size(pyaudio.paInt16)
    while True:
        # Convert at a set rate the data that comes in from recording thread
        if is_active_transcriber and audio_type and not myqueue.empty():
            current_time = datetime.utcnow()
            # Set next_convert_instance for first time
            next_convert_instance = next_convert_instance or current_time + convert_frequency

            # To improve accuracy of transcriptions and lessen strain on the GPU,
            # only run transcription every few, but transcription does not happen instantly.
            # Instant transcription is not accurate and there is still some latency
            if current_time > next_convert_instance:
                next_convert_instance += convert_frequency
                sentence_completed = False
                while not myqueue.empty():
                    content_data = myqueue.get()
                    power = audioop.rms(content_data, sample_size)
                    quiet_samples = quiet_samples + 1 if power < power_slider.value else 0

                    # If there is sufficient silence start over bufer and add a new line
                    if quiet_samples > AUDIO_SAMPLING_FREQ / FPB * quiet_time:
                        sentence_completed = True
                        last_sample = bytes()
                    last_sample += content_data

                # Save the raw frames as a WAV file
                audio_wav_file = io.BytesIO()
                wav_writer:wave.Wave_write = wave.open(audio_wav_file, "wb")
                wav_writer.setframerate(AUDIO_SAMPLING_FREQ)
                wav_writer.setsampwidth(paudio.get_sample_size(pyaudio.paInt16))
                wav_writer.setnchannels(1)
                wav_writer.writeframes(last_sample)
                wav_writer.close()

                # Read the audio data excluding wave headers
                audio_wav_file.seek(0)
                wav_reader:wave.Wave_read = wave.open(audio_wav_file)
                samples = wav_reader.getnframes()
                audio = wav_reader.readframes(samples)
                wav_reader.close()

                # https://stackoverflow.com/a/62298670
                # Convert wave data to a numpy array for the type
                audio_as_np_int16 = numpy.frombuffer(audio, dtype=numpy.int16)
                audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)
                audio_normalised = audio_as_np_float32 / LARGEST_SHORT_INT16

                selected_lang = None
                if lang_selector.value != 'Auto':
                    selected_lang = lang_selector.value

                activity = 'transcribe'
                if selected_lang != 'en' and translate_lang_box.value:
                    activity = 'translate'

                result = audio_type.transcribe(audio_normalised, language=selected_lang, task=activity)
                text = result['text'].strip()

                text_color = None
                if text_bg_box.value:
                    text_color = ft.colors.BLACK if nightmode_box.value else ft.colors.WHITE

                if not sentence_completed and convertion_lst.controls:
                    convertion_lst.controls[-1].value = text
                elif not convertion_lst.controls or (convertion_lst.controls and convertion_lst.controls[-1].value):
                    # Adding another item: always if list is empty, and if not empty add only if previous item is not an empty str
                    # Most appends are empty str since quiet period triggers sentence_completed
                    convertion_lst.controls.append(ft.Text(text, selectable=True, size=int(text_size_selector.value), bgcolor=text_color))
                convertion_lst.update()

                # If time permitted for recording is up we add an empty line to indicate that the buffer needs to be broken up
                audio_duration_in_seconds  = samples / float(AUDIO_SAMPLING_FREQ)
                if audio_duration_in_seconds > upper_limit_record_time:
                    last_sample = bytes()
                    convertion_lst.controls.append(ft.Text('', selectable=True, size=int(text_size_selector.value), bgcolor=text_color))
        sleep(0.1)

if __name__ == "__main__":
    ft.app(target=main)