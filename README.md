# 🎸 AI Chord Analyzer

An AI-powered web application that analyzes a song and generates a synchronized chord timeline.

Paste a YouTube URL, analyze the audio, and see the detected chords change in real time while the song plays.

## ✨ Features

- 🎵 YouTube song analysis
- 🎸 Automatic chord detection
- 🎼 Song key estimation
- 🥁 BPM detection
- ⏱️ Synchronized chord timeline
- ▶️ Audio playback
- 🔄 Chord smoothing and neighboring-chord cleanup
- 📊 Unique chord statistics
- 📈 Chord duration breakdown
- 🎹 Chord progression visualization
- 🖱️ Click any chord to jump to that point in the song
- 🌐 FastAPI backend
- 🐳 Docker deployment support
- ⚡ Responsive web interface

---

## 🧠 How It Works

The current version uses an audio-analysis pipeline rather than a large neural network.

```text
YouTube URL
     │
     ▼
   yt-dlp
     │
     ▼
 Downloaded Audio
     │
     ▼
   FFmpeg
     │
     ▼
      WAV
     │
     ▼
  Librosa
     │
     ▼
 Chroma CQT
     │
     ▼
Chord Detection
     │
     ▼
 Smoothing
     │
     ▼
Merge Neighboring
Identical Chords
     │
     ▼
Chord Timeline
     │
     ▼
     Web UI
```

### Chord Detection

The current implementation extracts chroma features using **Chroma CQT** and compares the resulting harmonic representation against major and minor chord templates.

The detected chords are then smoothed to reduce short-lived noisy predictions and neighboring identical chords are merged into larger segments.

This provides a lightweight baseline that is fast enough for an MVP without requiring model training or GPU inference.

---

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Librosa
- NumPy
- SciPy
- yt-dlp
- FFmpeg

### Frontend

- HTML
- CSS
- Vanilla JavaScript

### Deployment

- Docker
- Render

---

## 📁 Project Structure

```text
chord-analyzer/
│
├── Dockerfile
├── .gitignore
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── audio_downloader.py
│   ├── chord_detector.py
│   ├── requirements.txt
│   │
│   └── temp/
│       └── .gitkeep
│
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

---

# 🚀 Running Locally

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/chord-analyzer.git

cd chord-analyzer
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 2. Install Python

Python 3.11 is recommended.

Check your version:

```bash
python --version
```

---

## 3. Install FFmpeg

FFmpeg is required by `yt-dlp` and the audio conversion pipeline.

Verify that it is available:

```bash
ffmpeg -version
```

You should also be able to run:

```bash
ffprobe -version
```

If Windows cannot find FFmpeg, add the directory containing `ffmpeg.exe` to your system PATH.

You can verify the executable location with:

```bash
where ffmpeg
```

---

## 4. Create a virtual environment

From the project root:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

---

## 5. Install dependencies

```bash
pip install -r backend/requirements.txt
```

---

## 6. Start the FastAPI server

From the project root:

```bash
uvicorn backend.main:app --reload
```

The application will run at:

```text
http://localhost:8000
```

Open that address in your browser.

---

# 🐳 Running with Docker

The project includes a Dockerfile that installs FFmpeg inside the container, so FFmpeg does not need to be installed separately inside the deployment environment.

Build the image:

```bash
docker build -t chord-analyzer .
```

Run it:

```bash
docker run -p 8000:8000 chord-analyzer
```

Then open:

```text
http://localhost:8000
```

---

# ☁️ Deploying to Render

The application is designed to run as a Docker-based Render Web Service.

### 1. Push the project to GitHub

Make sure your repository contains:

```text
Dockerfile
backend/
frontend/
requirements.txt
.gitignore
README.md
```

Do **not** commit generated audio files.

---

### 2. Create a Render Web Service

Create a new Web Service and connect your GitHub repository.

Use Docker as the runtime.

Render will build the application using:

```text
Dockerfile
```

The Docker container installs:

- Python
- FFmpeg
- Python dependencies
- FastAPI application

---

### 3. Render command

The Dockerfile starts FastAPI using Render's assigned port:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
```

The frontend is served directly by FastAPI, so only one web service is required.

---

# 🎧 Audio File Handling

Generated audio files are stored temporarily in:

```text
backend/temp/
```

The application does not permanently keep downloaded audio.

Old generated audio files are automatically removed after the configured TTL.

The current default is:

```python
AUDIO_TTL_SECONDS = 60 * 60
```

which means approximately **60 minutes**.

Generated audio files should never be committed to Git.

---

# 🔌 API

## `GET /api`

Checks whether the API is running.

Example response:

```json
{
    "status": "ok",
    "message": "AI Chord Analyzer API is running"
}
```

---

## `POST /analyze`

Analyzes a YouTube URL.

### Request

```json
{
    "youtube_url": "https://www.youtube.com/watch?v=..."
}
```

### Response

```json
{
    "success": true,
    "data": {
        "duration": 234.5,
        "bpm": 120,
        "key": "G",
        "segments": [
            {
                "start": 0.0,
                "end": 3.7,
                "end": 7.4,
                "chord": "G",
                "confidence": 0.91
            }
        ],
        "audio_url": "http://localhost:8000/audio/example.wav"
    }
}
```

---

# 🎸 Chord Timeline

Each detected chord is represented as a segment:

```json
{
    "start": 0.0,
    "end": 3.7,
    "chord": "G",
    "confidence": 0.91
}
```

The frontend uses these timestamps to synchronize the displayed chord with the audio player.

When the song reaches a chord segment, that chord becomes active in the UI.

Users can also click a chord to jump directly to its start time.

---

# 📊 Chord Statistics

The application distinguishes between:

### Timeline segments

Every detected chord segment.

For example:

```text
G → C → G → Em → G → C → G
```

contains 7 timeline segments.

### Unique chords

The number of different chord names:

```text
G
C
Em
```

The UI reports **3 unique chords**.

---

# 🔮 Future Development

The current implementation is intentionally lightweight. Future versions could include:

### 🎸 Guitar-specific features

- Chord diagrams
- Guitar fingerings
- Alternative voicings
- Capo detection
- Suggested capo position
- Barre-chord alternatives
- Open-chord alternatives

### 🎵 Music analysis

- Strumming pattern detection
- Chord progression recognition
- Verse / chorus / bridge detection
- Tempo changes
- Time-signature detection
- Song structure analysis

### 🤖 Machine Learning

The current template-based approach could eventually be replaced or enhanced with a neural chord-recognition model.

Potential future pipeline:

```text
Audio
  ↓
Source Separation
  ↓
Guitar / Harmonic Signal
  ↓
Neural Chord Recognition
  ↓
Chord + Voicing Detection
  ↓
Guitar-Friendly Representation
```

A future version could also explore datasets such as GuitarSet and other music transcription datasets.

---

# ⚠️ Current Limitations

The current system primarily detects **harmonic chord content from the overall audio**.

It does not necessarily identify the exact guitar voicing being played.

For example, these can represent the same harmonic chord:

```text
C major

x32010
x35553
8-10-10-9-8-8
```

Audio-based chord recognition may correctly identify all of them as `C`, but determining which physical guitar voicing was actually played requires additional information and more advanced modeling.

The current detector also focuses primarily on major and minor chords. Extended chords such as:

```text
Cmaj7
Dm7
G7
Am9
F#dim
```

are not yet fully modeled.

---

# 🔒 Copyright & Usage

This project is intended primarily for research, experimentation, and personal use.

The application currently accepts YouTube URLs for audio analysis. Users are responsible for ensuring that they have the necessary rights or permissions to access and analyze the audio they submit.

For a public production service, the audio acquisition and playback architecture should be reviewed for compliance with the terms of the relevant platforms and copyright law.

A future production version may instead use user-uploaded or otherwise authorized audio.

---

# 📌 Project Status

**MVP — Functional**

Current pipeline:

```text
YouTube URL
      ↓
Audio Download
      ↓
FFmpeg Conversion
      ↓
Chroma Analysis
      ↓
Chord Detection
      ↓
Smoothing
      ↓
Chord Merging
      ↓
Synchronized Web UI
```

The goal is to evolve this from a basic chord detector into a complete **AI-powered guitar learning and song analysis tool**.

---

## 👨‍💻 Author

Built as an independent music-tech / machine-learning project.

If you find the project interesting, feel free to ⭐ the repository and follow the development.
