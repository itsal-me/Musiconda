import numpy as np
import librosa
from scipy.ndimage import median_filter


NOTE_NAMES = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]


# ---------------------------------------------------------
# CHORD TEMPLATES
# ---------------------------------------------------------

def normalize_vector(vector):
    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def create_chord_templates():
    templates = {}

    major_intervals = [0, 4, 7]
    minor_intervals = [0, 3, 7]

    for root_index, root_name in enumerate(NOTE_NAMES):

        # Major
        template = np.zeros(12)

        for interval in major_intervals:
            template[(root_index + interval) % 12] = 1

        templates[f"{root_name}"] = normalize_vector(template)

        # Minor
        template = np.zeros(12)

        for interval in minor_intervals:
            template[(root_index + interval) % 12] = 1

        templates[f"{root_name}m"] = normalize_vector(template)

    return templates


CHORD_TEMPLATES = create_chord_templates()


# ---------------------------------------------------------
# CHORD DETECTION
# ---------------------------------------------------------

def detect_chord(chroma_frame):
    """
    Compare a chroma vector against every chord template.
    Returns:
        chord
        confidence
    """

    chroma_frame = normalize_vector(chroma_frame)

    best_chord = "N"
    best_score = -1

    for chord_name, template in CHORD_TEMPLATES.items():

        score = float(np.dot(chroma_frame, template))

        if score > best_score:
            best_score = score
            best_chord = chord_name

    return best_chord, best_score


# ---------------------------------------------------------
# SMOOTH CHORDS
# ---------------------------------------------------------

def smooth_chords(chords, size=15):

    if len(chords) < 3:
        return chords

    # Median filter requires numeric labels
    unique_chords = list(dict.fromkeys(chords))

    chord_to_number = {
        chord: index
        for index, chord in enumerate(unique_chords)
    }

    number_to_chord = {
        index: chord
        for chord, index in chord_to_number.items()
    }

    numeric = np.array([
        chord_to_number[chord]
        for chord in chords
    ])

    smoothed = median_filter(
        numeric,
        size=size,
        mode="nearest"
    )

    return [
        number_to_chord[int(value)]
        for value in smoothed
    ]


# ---------------------------------------------------------
# MERGE CONSECUTIVE CHORDS
# ---------------------------------------------------------

def merge_chords(times, chords, confidences, min_duration=0.5):

    if len(chords) == 0:
        return []

    segments = []

    current_chord = chords[0]
    start_time = float(times[0])

    confidence_values = [float(confidences[0])]

    for i in range(1, len(chords)):

        chord = chords[i]

        if chord != current_chord:

            end_time = float(times[i])

            if end_time - start_time >= min_duration:

                segments.append({
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "chord": current_chord,
                    "confidence": round(
                        float(np.mean(confidence_values)),
                        3
                    )
                })

            current_chord = chord
            start_time = end_time
            confidence_values = [float(confidences[i])]

        else:

            confidence_values.append(
                float(confidences[i])
            )

    # Last segment
    end_time = float(times[-1])

    if end_time - start_time >= min_duration:

        segments.append({
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "chord": current_chord,
            "confidence": round(
                float(np.mean(confidence_values)),
                3
            )
        })

    # Merge again if smoothing created tiny gaps
    final_segments = []

    for segment in segments:

        if (
            final_segments
            and final_segments[-1]["chord"]
            == segment["chord"]
        ):

            final_segments[-1]["end"] = segment["end"]

            final_segments[-1]["confidence"] = round(
                (
                    final_segments[-1]["confidence"]
                    + segment["confidence"]
                ) / 2,
                3
            )

        else:

            final_segments.append(segment)

    return final_segments


# ---------------------------------------------------------
# KEY DETECTION
# ---------------------------------------------------------

MAJOR_PROFILE = np.array([
    6.35,
    2.23,
    3.48,
    2.33,
    4.38,
    4.09,
    2.52,
    5.19,
    2.39,
    3.66,
    2.29,
    2.88
])


MINOR_PROFILE = np.array([
    6.33,
    2.68,
    3.52,
    5.38,
    2.60,
    3.53,
    2.54,
    4.75,
    3.98,
    2.69,
    3.34,
    3.17
])


def estimate_key(chroma):

    average_chroma = np.mean(
        chroma,
        axis=1
    )

    average_chroma = normalize_vector(
        average_chroma
    )

    best_key = "C"
    best_score = -999

    for root in range(12):

        # Rotate profile
        major_profile = np.roll(
            MAJOR_PROFILE,
            root
        )

        minor_profile = np.roll(
            MINOR_PROFILE,
            root
        )

        major_profile = normalize_vector(
            major_profile
        )

        minor_profile = normalize_vector(
            minor_profile
        )

        major_score = np.dot(
            average_chroma,
            major_profile
        )

        minor_score = np.dot(
            average_chroma,
            minor_profile
        )

        if major_score > best_score:

            best_score = major_score

            best_key = (
                f"{NOTE_NAMES[root]} major"
            )

        if minor_score > best_score:

            best_score = minor_score

            best_key = (
                f"{NOTE_NAMES[root]} minor"
            )

    return best_key


# ---------------------------------------------------------
# MAIN AUDIO ANALYSIS
# ---------------------------------------------------------

def analyze_audio(audio_file):

    print("Loading audio...")

    y, sr = librosa.load(
        audio_file,
        sr=22050,
        mono=True
    )

    duration = librosa.get_duration(
        y=y,
        sr=sr
    )

    print(
        f"Audio duration: {duration:.2f}s"
    )

    # -----------------------------------------------------
    # CHROMA
    # -----------------------------------------------------

    print("Extracting chroma...")

    hop_length = 512

    chroma = librosa.feature.chroma_cqt(
        y=y,
        sr=sr,
        hop_length=hop_length
    )

    # -----------------------------------------------------
    # BPM
    # -----------------------------------------------------

    print("Estimating BPM...")

    tempo, _ = librosa.beat.beat_track(
        y=y,
        sr=sr
    )

    try:
        bpm = float(np.asarray(tempo).flatten()[0])
    except Exception:
        bpm = 0

    # -----------------------------------------------------
    # RAW CHORD DETECTION
    # -----------------------------------------------------

    print("Detecting chords...")

    chords = []
    confidences = []
    times = []

    frame_times = librosa.frames_to_time(
        np.arange(chroma.shape[1]),
        sr=sr,
        hop_length=hop_length
    )

    for i in range(chroma.shape[1]):

        frame = chroma[:, i]

        chord, confidence = detect_chord(
            frame
        )

        chords.append(chord)
        confidences.append(confidence)
        times.append(frame_times[i])

    # -----------------------------------------------------
    # SMOOTH
    # -----------------------------------------------------

    print("Smoothing chord sequence...")

    chords = smooth_chords(
        chords,
        size=15
    )

    # -----------------------------------------------------
    # MERGE
    # -----------------------------------------------------

    print("Creating chord segments...")

    segments = merge_chords(
        times,
        chords,
        confidences,
        min_duration=0.5
    )

    # -----------------------------------------------------
    # KEY
    # -----------------------------------------------------

    print("Estimating key...")

    key = estimate_key(
        chroma
    )

    # -----------------------------------------------------
    # CHORD STATISTICS
    # -----------------------------------------------------

    chord_duration = {}

    for segment in segments:

        chord = segment["chord"]

        duration_value = (
            segment["end"]
            - segment["start"]
        )

        chord_duration[chord] = (
            chord_duration.get(chord, 0)
            + duration_value
        )

    return {
        "duration": round(
            float(duration),
            2
        ),

        "bpm": round(
            float(bpm),
            1
        ),

        "key": key,

        "segments": segments,

        "chord_duration": {
            chord: round(
                duration,
                2
            )
            for chord, duration
            in chord_duration.items()
        }
    }