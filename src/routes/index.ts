import { Router } from "express";

export const indexRouter = Router();

indexRouter.get("/", (_req, res) => {
  res.render("index", { activeTab: "about" });
});
