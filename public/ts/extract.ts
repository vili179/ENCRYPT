declare function showToast(
  message: string,
  type?: "error" | "success" | "info"
): void;
declare function setupFileDrop(
  dropId: string,
  inputId: string,
  readyText: string
): void;

setupFileDrop("exDrop", "exFile", "ready for extraction");

const extractForm = document.querySelector("form") as HTMLFormElement | null;
const fileIn = document.getElementById("exFile") as HTMLInputElement | null;

if (extractForm) {
  extractForm.addEventListener("submit", (e) => {
    if (!fileIn?.files?.[0]) {
      e.preventDefault();
      showToast("Please select a stego image (PNG, JPEG, HEIC).", "error");
      return;
    }
    const pwd = (document.getElementById("exPwd") as HTMLInputElement)?.value;
    if (!pwd?.trim()) {
      e.preventDefault();
      showToast("Please enter the decryption password.", "error");
      return;
    }
    const loading = document.getElementById("extractLoading");
    if (loading) loading.classList.add("show");
  });
}

document.getElementById("copyBtn")?.addEventListener("click", () => {
  const txt = document.getElementById("resultText")?.textContent || "";
  if (!txt) return;
  navigator.clipboard.writeText(txt).then(() => {
    showToast("Copied to clipboard!", "success");
  });
});

document.getElementById("clearBtn")?.addEventListener("click", () => {
  const box = document.querySelector(".result-box") as HTMLElement | null;
  if (box) box.style.display = "none";
});

const resultText = document.getElementById("resultText");
if (resultText && resultText.textContent) {
  const fullText = resultText.textContent;
  resultText.textContent = "";
  let i = 0;
  const speed = Math.max(15, Math.min(50, 500 / fullText.length));
  const timer = setInterval(() => {
    if (i < fullText.length) {
      resultText.textContent += fullText[i];
      i++;
    } else {
      clearInterval(timer);
    }
  }, speed);
}
