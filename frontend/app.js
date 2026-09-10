// Local development:
//   http://localhost:5500 -> backend http://localhost:8000
//
// Render:
//   frontend + backend are served from the same domain
//
// If the page is running on port 5500, use port 8000.
// Otherwise, use the current origin.

const API_URL =
    window.location.port === "5500"
        ? "http://localhost:8000"
        : window.location.origin;

// ---------------------------------------------------------
// ELEMENTS
// ---------------------------------------------------------

const youtubeInput = document.getElementById("youtubeUrl");

const analyzeButton = document.getElementById("analyzeButton");

const status = document.getElementById("status");

const statusText = document.getElementById("statusText");

const results = document.getElementById("results");

const errorBox = document.getElementById("error");

const audioPlayer = document.getElementById("audioPlayer");

const chordTimeline = document.getElementById("chordTimeline");

const progression = document.getElementById("progression");

const chordBreakdown = document.getElementById("chordBreakdown");

const keyDisplay = document.getElementById("keyDisplay");

const keyStat = document.getElementById("keyStat");

const bpmStat = document.getElementById("bpmStat");

const durationStat = document.getElementById("durationStat");

const chordCountStat = document.getElementById("chordCountStat");

// ---------------------------------------------------------
// GLOBAL DATA
// ---------------------------------------------------------

let chordSegments = [];

// ---------------------------------------------------------
// FORMAT TIME
// ---------------------------------------------------------

function formatTime(seconds) {
    seconds = Math.max(0, Math.floor(seconds));

    const minutes = Math.floor(seconds / 60);

    const remainingSeconds = seconds % 60;

    return (
        String(minutes).padStart(2, "0") +
        ":" +
        String(remainingSeconds).padStart(2, "0")
    );
}

// ---------------------------------------------------------
// ANALYZE BUTTON
// ---------------------------------------------------------

analyzeButton.addEventListener("click", analyzeSong);

// ---------------------------------------------------------
// ENTER KEY
// ---------------------------------------------------------

youtubeInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        analyzeSong();
    }
});

// ---------------------------------------------------------
// ANALYZE SONG
// ---------------------------------------------------------

async function analyzeSong() {
    const url = youtubeInput.value.trim();

    if (!url) {
        showError("Please paste a YouTube URL.");

        return;
    }

    hideError();

    results.classList.add("hidden");

    status.classList.remove("hidden");

    analyzeButton.disabled = true;

    statusText.textContent = "Downloading and analyzing audio...";

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                youtube_url: url,
            }),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Analysis failed.");
        }

        if (!result.success) {
            throw new Error("Analysis failed.");
        }

        displayResults(result.data);
    } catch (error) {
        console.error(error);

        showError(error.message || "Something went wrong.");
    } finally {
        status.classList.add("hidden");

        analyzeButton.disabled = false;
    }
}

// ---------------------------------------------------------
// DISPLAY RESULTS
// ---------------------------------------------------------

function displayResults(data) {
    results.classList.remove("hidden");

    chordSegments = data.segments || [];

    // -------------------------------------------------
    // STATS
    // -------------------------------------------------

    keyDisplay.textContent = data.key || "Unknown";

    keyStat.textContent = data.key || "—";

    bpmStat.textContent = data.bpm ? `${data.bpm} BPM` : "—";

    durationStat.textContent = formatTime(data.duration || 0);

    // Count unique chords instead of timeline segments
    const uniqueChords = new Set(chordSegments.map((segment) => segment.chord));

    chordCountStat.textContent = uniqueChords.size;

    // -------------------------------------------------
    // LOAD AUDIO
    // -------------------------------------------------

    if (data.audio_url) {
        audioPlayer.src = data.audio_url;

        audioPlayer.load();
    }

    // -------------------------------------------------
    // RENDER
    // -------------------------------------------------

    renderChordTimeline();

    renderProgression();

    renderBreakdown();
}

// ---------------------------------------------------------
// RENDER CHORD TIMELINE
// ---------------------------------------------------------

function renderChordTimeline() {
    chordTimeline.innerHTML = "";

    chordSegments.forEach((segment, index) => {
        const element = document.createElement("div");

        element.className = "chord";

        element.dataset.index = index;

        element.innerHTML = `

                <span class="chord-name">
                    ${escapeHTML(segment.chord)}
                </span>

                <span class="chord-time">
                    ${formatTime(segment.start)}
                </span>

            `;

        element.addEventListener("click", () => {
            audioPlayer.currentTime = segment.start;

            audioPlayer.play();
        });

        chordTimeline.appendChild(element);
    });
}

// ---------------------------------------------------------
// RENDER PROGRESSION
// ---------------------------------------------------------

function renderProgression() {
    progression.innerHTML = "";

    // Avoid showing repeated adjacent chords

    const uniqueSequence = [];

    chordSegments.forEach((segment) => {
        const previous = uniqueSequence[uniqueSequence.length - 1];

        if (previous !== segment.chord) {
            uniqueSequence.push(segment.chord);
        }
    });

    uniqueSequence.forEach((chord, index) => {
        const chordElement = document.createElement("span");

        chordElement.className = "progression-chord";

        chordElement.textContent = chord;

        progression.appendChild(chordElement);

        if (index < uniqueSequence.length - 1) {
            const arrow = document.createElement("span");

            arrow.className = "arrow";

            arrow.textContent = "→";

            progression.appendChild(arrow);
        }
    });
}

// ---------------------------------------------------------
// RENDER BREAKDOWN
// ---------------------------------------------------------

function renderBreakdown() {
    chordBreakdown.innerHTML = "";

    const entries = Object.entries(getChordDurations());

    entries.sort((a, b) => b[1] - a[1]);

    entries.forEach(([chord, duration]) => {
        const element = document.createElement("div");

        element.className = "breakdown-item";

        element.innerHTML = `

                <strong>
                    ${escapeHTML(chord)}
                </strong>

                <span>
                    ${formatTime(duration)}
                </span>

            `;

        chordBreakdown.appendChild(element);
    });
}

// ---------------------------------------------------------
// CHORD DURATIONS
// ---------------------------------------------------------

function getChordDurations() {
    const durations = {};

    chordSegments.forEach((segment) => {
        const duration = segment.end - segment.start;

        durations[segment.chord] = (durations[segment.chord] || 0) + duration;
    });

    return durations;
}

// ---------------------------------------------------------
// AUDIO SYNCHRONIZATION
// ---------------------------------------------------------

audioPlayer.addEventListener("timeupdate", () => {
    const currentTime = audioPlayer.currentTime;

    const activeIndex = chordSegments.findIndex(
        (segment) => currentTime >= segment.start && currentTime < segment.end,
    );

    updateActiveChord(activeIndex);
});

// ---------------------------------------------------------
// ACTIVE CHORD
// ---------------------------------------------------------

function updateActiveChord(index) {
    const chordElements = document.querySelectorAll(".chord");

    chordElements.forEach((element) => {
        element.classList.remove("active");
    });

    if (index >= 0) {
        const activeElement = document.querySelector(
            `.chord[data-index="${index}"]`,
        );

        if (activeElement) {
            activeElement.classList.add("active");

            activeElement.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
                inline: "center",
            });
        }
    }
}

// ---------------------------------------------------------
// ERROR
// ---------------------------------------------------------

function showError(message) {
    errorBox.textContent = message;

    errorBox.classList.remove("hidden");
}

function hideError() {
    errorBox.classList.add("hidden");
}

// ---------------------------------------------------------
// SECURITY
// ---------------------------------------------------------

function escapeHTML(value) {
    const div = document.createElement("div");

    div.textContent = String(value);

    return div.innerHTML;
}
