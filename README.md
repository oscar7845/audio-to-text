# Audio to Text Converter
This desktop application...
## Inspiration
So, you know how during Zoom lectures or in class lectures you sometimes space out, miss something, and then don't want to interrupt thr professor to ask them to repeat? In these circumstances, the fear of interrupting creates an obstacle to effective learning. Or perhaps you simply want a way to master learning as you wont miss a single word the professor said in the lecture. 
## What it does
It transcribes spoken words into written text in order to turn any audio source into readable material. It is designed to handle lectures and other educational content so that students can focus on the material without worrying about missing crucial points. For in class lectures, you will need to sit in the front rows as if you sit in the back the transcription wont be accurate. It can also transcribe audio from other sources such as youtube videos, recorded lectures, or podcasts.
## How it was built
Python packages PyAudio, torch, and Whisper were used to handle the audio data, process it and convert it into text form. PyAudio opens an audio stream that captures live audio data handled in a separate thread to keep the GUI responsive. Whisper library converts the audio stream into text. This text transcription happens in real time with frequent updates. When a transcription starts parameters are saved in current_app_params.yaml. During transcription the application automatically breaks it up into lines based on lines_quiet_time_in_sec. This parameter sets how much audio with volume lower than the volume threshold is required to break up the transcription into separate lines. The convert_frequency_seconds defines how often the audio data should be transcribed, in seconds. The upper_limit_record_time defines the maximum amount of time a recording should be transcribed. These parameters can be changed only from the current_app_params.yaml.  When stopping the transcription, lines are saved into content.txt. 
## Challenges
PyInstaller sometimes has trouble finding and including certain files during the packaging process. When creating the .exe file, pyinstaller couldt find some whisper files (mel_filters.npz and ultilingual.tiktoken). A solution I found for this error is telling pyinstaller to include these files. It can be done in the .spec file by adding the destination of the files in datas.
datas=[
        ('C:\\vsCode\\audio-to-text\\env\\lib\\site-packages\\whisper\\assets\\mel_filters.npz', 'whisper\\assets\\'),
        ('C:\\vsCode\\audio-to-text\\env\\lib\\site-packages\\whisper\\assets\\multilingual.tiktoken', 'whisper\\assets\\')
    ],
## What was learned
During this project I learned how to use multiple libraries such as PyAudio, Whisper, and Flet, and integrate them into one functioning system. I gained an understanding of threading and I got familiar with audio processing concepts.
## What's next
The next step would be to further enhance the application by adding some functionalities such as automatic topic segmentation and sentiment analysis so that you can understand the speaker's tone which is pretty fire. This has the potential to assist many people affected by the anxieties associated with learning and find ways to make learning easier by creating new ways of interacting with the lecture materials.