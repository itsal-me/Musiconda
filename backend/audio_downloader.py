import os
import uuid
import glob
import subprocess
import shutil

import yt_dlp


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "temp"
)

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)


def download_audio(url):

    # -----------------------------------------------------
    # FIND FFMPEG
    # -----------------------------------------------------

    ffmpeg_path = shutil.which(
        "ffmpeg"
    )

    if ffmpeg_path is None:

        raise Exception(
            "FFmpeg was not found. "
            "Make sure FFmpeg/bin is added to PATH."
        )

    print(
        "FFmpeg:",
        ffmpeg_path
    )

    # -----------------------------------------------------
    # JOB ID
    # -----------------------------------------------------

    job_id = str(
        uuid.uuid4()
    )

    source_template = os.path.join(
        TEMP_DIR,
        f"{job_id}.%(ext)s"
    )

    output_wav = os.path.join(
        TEMP_DIR,
        f"{job_id}.wav"
    )

    # -----------------------------------------------------
    # YT-DLP
    # -----------------------------------------------------

    ydl_opts = {

        "format":
            "bestaudio/best",

        "outtmpl":
            source_template,

        "noplaylist":
            True,

        "quiet":
            False,

        "no_warnings":
            False,

        "ffmpeg_location":
            os.path.dirname(ffmpeg_path)
    }

    print(
        "Downloading audio..."
    )

    with yt_dlp.YoutubeDL(
        ydl_opts
    ) as ydl:

        ydl.download([
            url
        ])

    # -----------------------------------------------------
    # FIND SOURCE FILE
    # -----------------------------------------------------

    files = glob.glob(
        os.path.join(
            TEMP_DIR,
            f"{job_id}.*"
        )
    )

    source_file = None

    for file in files:

        if not file.endswith(
            ".wav"
        ):

            source_file = file
            break

    if source_file is None:

        raise Exception(
            "Downloaded audio file was not found."
        )

    print(
        "Downloaded:",
        source_file
    )

    # -----------------------------------------------------
    # CONVERT TO WAV
    # -----------------------------------------------------

    print(
        "Converting to WAV..."
    )

    command = [

        ffmpeg_path,

        "-y",

        "-i",
        source_file,

        "-ac",
        "1",

        "-ar",
        "22050",

        "-vn",

        output_wav
    ]

    print(
        "Running:",
        command
    )

    subprocess.run(
        command,
        check=True
    )

    # -----------------------------------------------------
    # REMOVE ORIGINAL
    # -----------------------------------------------------

    try:

        os.remove(
            source_file
        )

    except Exception:

        pass

    print(
        "Final WAV:",
        output_wav
    )

    return output_wav