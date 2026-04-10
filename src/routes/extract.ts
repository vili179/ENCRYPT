import { Router } from "express";
import multer from "multer";
import { revealMessage } from "../services/steganography.js";
import { isAllowedFile } from "../utils/validation.js";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

export const extractRouter = Router();

extractRouter.get("/extract", (_req, res) => {
  res.render("extract", { activeTab: "extract", error: null, result: null });
});

extractRouter.post("/extract", upload.single("image"), async (req, res) => {
  try {
    const file = req.file;
    const password = req.body.password as string;

    if (!file || !isAllowedFile(file.originalname)) {
      res.render("extract", {
        activeTab: "extract",
        error: "Unsupported file type. Use PNG, JPG, JPEG, HEIC, HEIF.",
        result: null,
      });
      return;
    }

    if (!password) {
      res.render("extract", {
        activeTab: "extract",
        error: "Please enter the decryption password.",
        result: null,
      });
      return;
    }

    const message = await revealMessage(file.buffer, password);
    res.render("extract", {
      activeTab: "extract",
      result: message,
      error: null,
    });
  } catch (err) {
    const errorMsg =
      err instanceof Error ? err.message : "An unexpected error occurred.";
    const displayError = errorMsg.includes("Incorrect password")
      ? "Incorrect password. Please try again with the correct key."
      : errorMsg;
    res.render("extract", {
      activeTab: "extract",
      error: displayError,
      result: null,
    });
  }
});
