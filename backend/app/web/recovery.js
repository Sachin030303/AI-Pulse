"use strict";

const isReset = window.location.pathname === "/reset-password";
const params = new URLSearchParams(window.location.hash.slice(1));
let resetToken = params.get("token");

// Remove the secret from the browser address bar immediately.
if (window.location.hash) {
  window.history.replaceState(null, "", window.location.pathname);
}

document.getElementById("forgot-panel").hidden = isReset;
document.getElementById("reset-panel").hidden = !isReset;

const forgotForm = document.getElementById("forgot-form");
const resetForm = document.getElementById("reset-form");

function setMessage(id, message) {
  document.getElementById(id).textContent = message;
}

async function postJSON(path, payload) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    credentials: "omit",
    referrerPolicy: "no-referrer",
    body: JSON.stringify(payload),
  });
}

forgotForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = forgotForm.querySelector("button");
  button.disabled = true;

  try {
    const email = document.getElementById("email").value;

    const response = await postJSON(
      "/api/v1/auth/forgot-password",
      { email }
    );

    if (response.ok) {
      setMessage(
        "forgot-message",
        "If the account exists, recovery instructions will be sent."
      );
    } else {
      setMessage(
        "forgot-message",
        "Recovery is temporarily unavailable. Please try later."
      );
    }
  } catch {
    setMessage("forgot-message", "Unable to connect to the server.");
  } finally {
    button.disabled = false;
  }
});

if (isReset && !resetToken) {
  setMessage(
    "reset-message",
    "This reset link is missing its token. Request a new link."
  );
  document.getElementById("reset-button").disabled = true;
}

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!resetToken) return;

  const password = document.getElementById("password").value;
  const confirmation = document.getElementById("confirmation").value;

  if (password !== confirmation) {
    setMessage("reset-message", "Passwords do not match.");
    return;
  }

  const button = document.getElementById("reset-button");
  button.disabled = true;

  try {
    const response = await postJSON(
      "/api/v1/auth/reset-password",
      {
        token: resetToken,
        new_password: password,
      }
    );

    if (response.ok) {
      resetToken = null;
      resetForm.reset();
      setMessage(
        "reset-message",
        "Password reset successful. You can sign in again."
      );
    } else {
      setMessage(
        "reset-message",
        "Unable to reset password. The link may be invalid or expired."
      );
    }
  } catch {
    setMessage("reset-message", "Unable to connect to the server.");
  } finally {
    button.disabled = !resetToken;
  }
});
