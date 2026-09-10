import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.audio_downloader import download_audio
from backend.chord_detector import analyze_audio


# =================================================
# PATHS
# =================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    BASE_DIR
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "temp"
)

FRONTEND_DIR = os.path.join(
    PROJECT_DIR,
    "frontend"
)

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)


# =================================================
# CONFIG
# =================================================

# Delete generated audio files older than 60 minutes.
AUDIO_TTL_SECONDS = 60 * 60


# =================================================
# APP
# =================================================

app = FastAPI(
    title="AI Chord Analyzer",
    version="1.0.0"
)


# =================================================
# CORS
# =================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =================================================
# REQUEST MODEL
# =================================================

class AnalyzeRequest(BaseModel):
    youtube_url: str


# =================================================
# CLEAN OLD AUDIO FILES
# =================================================

def cleanup_old_audio():
    """
    Delete generated audio files that are older
    than AUDIO_TTL_SECONDS.
    """

    now = time.time()

    for file_path in Path(TEMP_DIR).glob("*"):

        if not file_path.is_file():
            continue

        # Never delete .gitkeep
        if file_path.name == ".gitkeep":
            continue

        try:

            modified_time = file_path.stat().st_mtime

            age = now - modified_time

            if age > AUDIO_TTL_SECONDS:

                file_path.unlink(
                    missing_ok=True
                )

                print(
                    "Deleted old audio:",
                    file_path
                )

        except Exception as e:

            print(
                "Cleanup error:",
                repr(e)
            )


# =================================================
# ROOT / API STATUS
# =================================================

@app.get("/api")
def api_root():

    return {
        "status": "ok",
        "message": "AI Chord Analyzer API is running"
    }


# =================================================
# ANALYZE
# =================================================

@app.post("/analyze")
def analyze(
    request: Request,
    body: AnalyzeRequest
):

    url = body.youtube_url.strip()

    if not url:

        raise HTTPException(
            status_code=400,
            detail="YouTube URL is required."
        )

    try:

        # -----------------------------------------
        # CLEAN OLD FILES
        # -----------------------------------------

        cleanup_old_audio()


        # -----------------------------------------
        # DOWNLOAD AUDIO
        # -----------------------------------------

        print(
            "Downloading audio..."
        )

        audio_file = download_audio(
            url
        )

        print(
            "Audio file:",
            audio_file
        )


        # -----------------------------------------
        # ANALYZE AUDIO
        # -----------------------------------------

        print(
            "Analyzing audio..."
        )

        result = analyze_audio(
            audio_file
        )


        # -----------------------------------------
        # AUDIO URL
        # -----------------------------------------

        filename = os.path.basename(
            audio_file
        )

        audio_url = (
            f"{str(request.base_url).rstrip('/')}"
            f"/audio/{filename}"
        )

        result["audio_url"] = audio_url


        # -----------------------------------------
        # RESPONSE
        # -----------------------------------------

        return {
            "success": True,
            "data": result
        }


    except Exception as e:

        print(
            "ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =================================================
# SERVE AUDIO
# =================================================

@app.get("/audio/{filename}")
def serve_audio(
    filename: str
):

    # Prevent directory traversal
    safe_filename = os.path.basename(
        filename
    )

    file_path = os.path.join(
        TEMP_DIR,
        safe_filename
    )

    if not os.path.isfile(
        file_path
    ):

        raise HTTPException(
            status_code=404,
            detail="Audio file not found or expired."
        )

    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=safe_filename
    )


# =================================================
# SERVE FRONTEND
# =================================================

if os.path.isdir(FRONTEND_DIR):

    app.mount(
        "/",
        StaticFiles(
            directory=FRONTEND_DIR,
            html=True
        ),
        name="frontend"
    )