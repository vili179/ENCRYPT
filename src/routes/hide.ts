import { Router } from "express";
import multer from "multer";
import { hideMessage } from "../services/steganography.js";
import { isAllowedFile } from "../utils/validation.js";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

export const hideRouter = Router();

hideRouter.get("/hide", (_req, res) => {
  res.render("hide", { activeTab: "hide", error: null });
});

hideRouter.post("/hide", upload.single("image"), async (req, res) => {
  try {
    const file = req.file;
    const secret = req.body.secret as string;
    const password = req.body.password as string;

    if (!file || !isAllowedFile(file.originalname)) {
      res.render("hide", {
        activeTab: "hide",
        error: "Unsupported file type. Use PNG, JPG, JPEG, HEIC, HEIF.",
      });
      return;
    }

    if (!secret || !password) {
      res.render("hide", {
        activeTab: "hide",
        error: "Please fill in all fields.",
      });
      return;
    }

    const result = await hideMessage(file.buffer, secret, password);

    res.set({
      "Content-Type": "image/png",
      "Content-Disposition": 'attachment; filename="hidden_image.png"',
    });
    res.send(result.buffer);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "An unexpected error occurred.";
    res.render("hide", { activeTab: "hide", error: message });
  }
});
