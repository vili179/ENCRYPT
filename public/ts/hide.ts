declare function showToast(
  message: string,
  type?: "error" | "success" | "info"
): void;
declare function setupFileDrop(
  dropId: string,
  inputId: string,
  readyText: string
): void;

setupFileDrop("hideDrop", "hideFile", "ready");

const secretTextarea = document.getElementById(
  "hideSecret"
) as HTMLTextAreaElement | null;
const charCountEl = document.getElementById("charCount");

if (secretTextarea && charCountEl) {
  secretTextarea.addEventListener("input", () => {
    charCountEl.textContent = secretTextarea.value.length + " chars";
  });
}

const passwordInput = document.getElementById(
  "hidePassword"
) as HTMLInputElement | null;

if (passwordInput) {
  passwordInput.addEventListener("input", () => {
    const v = passwordInput.value;
    let s = 0;
    if (v.length >= 6) s++;
    if (v.length >= 10) s++;
    if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++;
    if (/[0-9!@#$%^&*]/.test(v)) s++;
    const colors = ["", "#ff3366", "#ffaa33", "#00ffaa", "#00ffcc"];
    for (let i = 1; i <= 4; i++) {
      const seg = document.getElementById("s" + i);
      if (seg) seg.style.background = i <= s ? colors[s] : "var(--border)";
    }
  });
}

const hideForm = document.querySelector("form") as HTMLFormElement | null;
const fileIn = document.getElementById("hideFile") as HTMLInputElement | null;

if (hideForm) {
  hideForm.addEventListener("submit", (e) => {
    if (!fileIn?.files?.[0]) {
      e.preventDefault();
      showToast("Please upload a carrier image (PNG, JPEG, HEIC).", "error");
      return;
    }
    if (!secretTextarea?.value.trim()) {
      e.preventDefault();
      showToast("Please enter a secret message.", "error");
      return;
    }
    if (!passwordInput?.value) {
      e.preventDefault();
      showToast("Please set a password.", "error");
      return;
    }
    const loading = document.getElementById("hideLoading");
    if (loading) loading.classList.add("show");
  });
}
