/**
 * voice.js — Web Speech API Integration
 * Handles microphone input (STT) and text-to-speech (TTS) for
 * the Rakshak AI multilingual emergency assistant.
 */

let isListening = false;
let recognition = null;

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Web Speech API not supported in this browser.");
    document.getElementById("micBtn").title = "Voice not supported in this browser";
    return null;
  }
  const r = new SpeechRecognition();
  r.continuous = false;
  r.interimResults = false;
  r.maxAlternatives = 1;
  return r;
}

function startListening(onResult) {
  recognition = initSpeechRecognition();
  if (!recognition) {
    alert("Voice recognition is not supported in your browser. Please use Chrome.");
    return;
  }
  recognition.lang = document.getElementById("langSelect")?.value || "en-IN";

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    onResult(transcript);
  };

  recognition.onerror = (e) => {
    console.error("Speech recognition error:", e.error);
    resetMicUI();
    if (e.error === "not-allowed") {
      addChatMessage("Please allow microphone access to use voice features.", "ai");
    }
  };

  recognition.onend = () => {
    resetMicUI();
  };

  recognition.start();
  isListening = true;
}

function stopListening() {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
  isListening = false;
  resetMicUI();
}

function toggleVoice() {
  if (isListening) {
    stopListening();
  } else {
    setMicActiveUI();
    startListening(async (transcript) => {
      addChatMessage(transcript, "user");
      resetMicUI();

      // Show typing indicator
      const typingId = showTypingIndicator();

      try {
        const reply = await askAssistant(transcript);
        removeTypingIndicator(typingId);
        addChatMessage(reply, "ai");
        speak(reply);
        // Animate waveform while speaking
        animateWaveform(true);
        setTimeout(() => animateWaveform(false), reply.length * 60);
      } catch (e) {
        removeTypingIndicator(typingId);
        const fallback = "I'm having connectivity issues. Please call 112 for immediate emergency assistance.";
        addChatMessage(fallback, "ai");
        speak(fallback);
      }
    });
  }
}

async function sendTextQuery() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";

  addChatMessage(text, "user");
  const typingId = showTypingIndicator();

  try {
    const reply = await askAssistant(text);
    removeTypingIndicator(typingId);
    addChatMessage(reply, "ai");
    speak(reply);
    animateWaveform(true);
    setTimeout(() => animateWaveform(false), reply.length * 60);
  } catch (e) {
    removeTypingIndicator(typingId);
    addChatMessage("Unable to connect. Please call 112 for emergencies.", "ai");
  }
}

function speak(text, lang) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel(); // stop any current speech
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang || document.getElementById("langSelect")?.value || "en-IN";
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  speechSynthesis.speak(utterance);
}

// ---- UI Helpers ----

function addChatMessage(text, role) {
  const history = document.getElementById("chatHistory");
  // Clear placeholder
  const placeholder = history.querySelector(".text-xs.text-center");
  if (placeholder) placeholder.remove();

  const div = document.createElement("div");
  div.className = role === "user" ? "chat-user" : "chat-ai";
  if (role === "ai") {
    div.innerHTML = `<span style="color:#ffb95f;font-size:10px;font-family:'JetBrains Mono',monospace;display:block;margin-bottom:2px">RAKSHAK AI</span>${text}`;
  } else {
    div.textContent = text;
  }
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;
}

function showTypingIndicator() {
  const history = document.getElementById("chatHistory");
  const id = "typing-" + Date.now();
  const div = document.createElement("div");
  div.id = id;
  div.className = "chat-ai";
  div.innerHTML = `<span style="color:#ffb95f;font-size:10px;font-family:'JetBrains Mono',monospace;display:block;margin-bottom:2px">RAKSHAK AI</span>
    <span style="opacity:0.6">Analyzing...</span>`;
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function setMicActiveUI() {
  const btn   = document.getElementById("micBtn");
  const label = document.getElementById("micLabel") || document.getElementById("micStatusLabel");
  if (btn) {
    btn.classList.add("recording-pulse");
    btn.style.borderColor = "#EF4444";
    btn.style.color       = "#EF4444";
  }
  if (label) label.textContent = "Listening... (tap to stop)";
}

function resetMicUI() {
  isListening = false;
  const btn   = document.getElementById("micBtn");
  const label = document.getElementById("micLabel") || document.getElementById("micStatusLabel");
  if (btn) {
    btn.classList.remove("recording-pulse");
    btn.style.borderColor = "";
    btn.style.color       = "";
  }
  if (label) label.textContent = "Tap to speak";
}

function animateWaveform(active) {
  const waveform = document.getElementById("waveform");
  if (waveform) waveform.style.opacity = active ? "1" : "0.5";
}
