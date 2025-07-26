# Use official Python 3.10 image
FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    vim \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/* 

# Set workdir
WORKDIR /app

# Copy requirements (if exists) and code
COPY ./requirements.txt ./requirements.txt
COPY . /app

# Install Python dependencies (compatible versions for OpenVoice v2, Whisper, TTS, etc.)
RUN pip install --upgrade pip \
#     && pip install numpy==1.24.3 scipy==1.10.1 librosa==0.10.1 numba==0.57.0 inflect==7.0.0 \
#     && pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu \
#     && pip install sounddevice==0.4.6 playsound==1.3.0 \
#     && pip install whisper==1.1.10 \
#     && pip install tts==0.17.6 \
    && pip install -r requirements.txt || true

RUN apt-get update && \
    apt-get install -y python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav gstreamer1.0-tools

# Download the required NLTK resource
RUN python3 -m nltk.downloader averaged_perceptron_tagger_eng

# Install OpenVoice v2 from source (assumes OpenVoice repo is in tts/OpenVoice)
RUN cd tts && rm -rf OpenVoice && git clone https://github.com/myshell-ai/OpenVoice.git
RUN cd tts/OpenVoice && pip install -e .
RUN pip install git+https://github.com/myshell-ai/MeloTTS.git
RUN python -m unidic download

# Expose port if needed (optional)
# EXPOSE 7860

# Set entrypoint
CMD ["python", "main.py"] 

# docker run -it \
#     --env PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
#     --volume ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \
#     --volume ~/.config/pulse/cookie:/root/.config/pulse/cookie \
#     --device /dev/snd \
#     your-image-name