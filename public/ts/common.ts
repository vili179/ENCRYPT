const saved = localStorage.getItem("enc-theme") || "dark";
if (saved === "light") {
  document.documentElement.setAttribute("data-theme", "light");
}

const themeToggle = document.getElementById("themeToggle");
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isLight =
      document.documentElement.getAttribute("data-theme") === "light";
    const next = isLight ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("enc-theme", next);
  });
}

function tick(): void {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toTimeString().slice(0, 8);
}
tick();
setInterval(tick, 1000);

document.addEventListener("click", (e) => {
  const btn = (e.target as HTMLElement).closest(
    "[data-toggle-pwd]"
  ) as HTMLElement | null;
  if (!btn) return;
  const id = btn.dataset.togglePwd!;
  const el = document.getElementById(id) as HTMLInputElement | null;
  if (!el) return;
  el.type = el.type === "password" ? "text" : "password";
  btn.textContent = el.type === "password" ? "\u{1F441}" : "\u{1F648}";
});

function showToast(
  message: string,
  type: "error" | "success" | "info" = "info"
): void {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    toast.addEventListener("transitionend", () => toast.remove());
  }, 3500);
}

function setupFileDrop(
  dropId: string,
  inputId: string,
  readyText: string
): void {
  const drop = document.getElementById(dropId);
  const fileIn = document.getElementById(inputId) as HTMLInputElement | null;
  if (!drop || !fileIn) return;

  drop.addEventListener("click", () => fileIn.click());

  fileIn.addEventListener("change", () => {
    const file = fileIn.files?.[0];
    if (!file) return;
    drop.classList.add("has-file");
    const dropText = drop.querySelector(".drop-text");
    const dropSub = drop.querySelector(".drop-sub");
    if (dropText) dropText.textContent = "\u2713 " + file.name;
    if (dropSub)
      dropSub.textContent =
        (file.size / 1024).toFixed(1) + " KB \u00B7 " + readyText;

    const preview = drop.querySelector(
      ".drop-preview"
    ) as HTMLImageElement | null;
    if (preview && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.src = e.target?.result as string;
        preview.style.display = "block";
        const icon = drop.querySelector(".drop-icon") as HTMLElement | null;
        if (icon) icon.style.display = "none";
      };
      reader.readAsDataURL(file);
    }
  });

  drop.addEventListener("dragover", (e) => {
    e.preventDefault();
    drop.classList.add("dragover");
  });
  drop.addEventListener("dragleave", () => drop.classList.remove("dragover"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault();
    drop.classList.remove("dragover");
    const f = (e as DragEvent).dataTransfer?.files[0];
    if (
      f &&
      (f.type.includes("image/") || /\.(png|jpe?g|heic|heif)$/i.test(f.name))
    ) {
      const dt = new DataTransfer();
      dt.items.add(f);
      fileIn.files = dt.files;
      fileIn.dispatchEvent(new Event("change"));
    } else {
      showToast("Please upload a valid image (PNG, JPEG, HEIC).", "error");
    }
  });
}

(window as any).showToast = showToast;
(window as any).setupFileDrop = setupFileDrop;
