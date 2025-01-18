const BUTTON_STATES = {
    NO_AUDIO: "no_audio",
    LOADING: "loading",
    PLAYING: "playing",
};

let buttonState = BUTTON_STATES.NO_AUDIO;
let audioPlayer;
const textArea = document.getElementById("text-input");
const errorMessage = document.querySelector("#error-message");
let audioChunks = []; // Array to buffer incoming audio data chunks
let socket;

function initializeWebSocket() {
    // create a new WebSocket connection
    socket = new WebSocket(`ws://localhost:3000`);

    socket.addEventListener("open", () => {
        console.log("WebSocket connection established.");
        // No data is sent on connection
    });

    socket.addEventListener("message", (event) => {
        // console.log("Incoming event:", event);

        if (typeof event.data === "string") {
            console.log("Incoming text data:", event.data);

            let msg = JSON.parse(event.data);

            if (msg.type === "Open") {
                console.log("WebSocket opened 2");
            } else if (msg.type === "Error") {
                console.error("WebSocket error:", error);
                buttonState = BUTTON_STATES.NO_AUDIO;
                updatePlayButton();
            } else if (msg.type === "Close") {
                console.log("WebSocket closed");
                buttonState = BUTTON_STATES.NO_AUDIO;
                updatePlayButton();
            } else if (msg.type === "Flushed") {
                console.log("Flushed received");

                // All data received, now combine chunks and play audio
                const blob = new Blob(audioChunks, { type: "audio/wav" });

                if (window.MediaSource) {
                    console.log('MP4 audio is supported');
                    const audioContext = new AudioContext();

                    const reader = new FileReader();
                    reader.onload = function () {
                        const arrayBuffer = this.result;

                        audioContext.decodeAudioData(arrayBuffer, (buffer) => {
                            const source = audioContext.createBufferSource();
                            source.buffer = buffer;
                            source.connect(audioContext.destination);
                            source.start();

                            buttonState = BUTTON_STATES.PLAYING;
                            updatePlayButton();

                            source.onended = () => {
                                // Clear the buffer
                                audioChunks = [];
                                buttonState = BUTTON_STATES.NO_AUDIO;
                                updatePlayButton();
                                textArea.value = "";
                            };
                        });
                    };
                    reader.readAsArrayBuffer(blob);
                } else {
                    console.error('MP4 audio is NOT supported');
                }

                // Clear the buffer
                audioChunks = [];
            }
        }

        if (event.data instanceof Blob) {
            // Incoming audio blob data
            const blob = event.data;
            console.log("Incoming blob data:", blob);

            // Push each blob into the array
            audioChunks.push(blob);
        }
    });

    socket.addEventListener("close", () => {
        console.log("Close received");
        buttonState = BUTTON_STATES.NO_AUDIO;
        updateConnectButton();
    });

    socket.addEventListener("error", (error) => {
        console.error("WebSocket error:", error);
        buttonState = BUTTON_STATES.NO_AUDIO;
        updateConnectButton();
    });
}


// Function to update the play button based on the current state
function updatePlayButton() {
    const playButton = document.getElementById("play-button");
    const icon = playButton.querySelector(".button-icon");

    switch (buttonState) {
        case BUTTON_STATES.NO_AUDIO:
            icon.className = "button-icon fa-solid fa-play";
            break;
        case BUTTON_STATES.LOADING:
            icon.className = "button-icon fa-solid fa-circle-notch";
            break;
        case BUTTON_STATES.PLAYING:
            icon.className = "button-icon fa-solid fa-stop";
            break;
        default:
            break;
    }
}

function updateConnectButton() {
    const connectButton = document.getElementById("connect-button");
    const icon = connectButton.querySelector(".button-icon");

    if (socket.readyState === WebSocket.OPEN) {
        icon.className = "button-icon fa-solid fa-link";
    } else {
        icon.className = "button-icon fa-solid fa-unlink";
    }
}

// Function to stop audio
function stopAudio() {
    audioPlayer = document.getElementById("audio-player");
    if (audioPlayer) {
        buttonState = BUTTON_STATES.PLAYING;
        updatePlayButton();
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioPlayer = null;
    }
}


document
    .getElementById("connect-button")
    .addEventListener("click", () => {
        initializeWebSocket();
    });

// window.onload = () => {
//     initializeWebSocket();
// }