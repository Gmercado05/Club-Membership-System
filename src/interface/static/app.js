const form = document.querySelector("#request-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const statusPill = document.querySelector("#status-pill");
const sendButton = document.querySelector("#send-button");
const quickActionButtons = document.querySelectorAll("[data-command]");
const sampleRegisterButton = document.querySelector("[data-sample-register]");
const sampleStatusButton = document.querySelector("[data-sample-status]");

const sampleRegisterCommands = [
  "Register Alice Chen, alice@example.com, Computer Science major, sophomore, start date 2026-06-01.",
  "Register John Doe, john@example.com, Computer Science major, junior, start date 2023-01-01, expiration date 2024-01-01.",
  "Register Maya Patel, maya@example.com, Biology major, senior, start date 2026-02-15, expiration date 2027-02-15.",
  "Register Carlos Rivera, carlos@example.com, Data Science major, freshman, start date 2026-09-20.",
];

let sampleRegisterIndex = 0;

const sampleStatusCommands = [
  "Check membership status for alice@example.com.",
  "Check membership status for john@example.com.",
  "Check membership status for maya@example.com.",
  "Check membership status for carlos@example.com.",
];

let sampleStatusIndex = 0;

function setStatus(text, state = "idle") {
  statusPill.textContent = text;
  statusPill.dataset.state = state;
}

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const speaker = document.createElement("span");
  speaker.className = "speaker";
  speaker.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("p");
  body.textContent = text;

  article.append(speaker, body);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

async function submitRequest(message) {
  const trimmed = message.trim();
  if (!trimmed) {
    input.focus();
    return;
  }

  appendMessage("user", trimmed);
  input.value = "";
  input.disabled = true;
  sendButton.disabled = true;
  setStatus("Working", "busy");

  try {
    const response = await fetch("/api/request", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: trimmed}),
    });

    const payload = await response.json();
    appendMessage("assistant", payload.formatted || "No response.");

    const status = payload.result && payload.result.status ? payload.result.status : "done";
    setStatus(status, status === "error" ? "error" : "idle");
  } catch (error) {
    appendMessage("assistant", `Request failed: ${error.message}`);
    setStatus("Error", "error");
  } finally {
    input.disabled = false;
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitRequest(input.value);
});

input.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    submitRequest(input.value);
  }
});

quickActionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.command;
    input.focus();
  });
});

if (sampleRegisterButton) {
  sampleRegisterButton.addEventListener("click", () => {
    input.value = sampleRegisterCommands[sampleRegisterIndex];
    sampleRegisterIndex = (sampleRegisterIndex + 1) % sampleRegisterCommands.length;
    input.focus();
  });
}

if (sampleStatusButton) {
  sampleStatusButton.addEventListener("click", () => {
    input.value = sampleStatusCommands[sampleStatusIndex];
    sampleStatusIndex = (sampleStatusIndex + 1) % sampleStatusCommands.length;
    input.focus();
  });
}
