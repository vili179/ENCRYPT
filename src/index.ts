import express from "express";
import compression from "compression";
import helmet from "helmet";
import { fileURLToPath } from "url";
import path from "path";

import { indexRouter } from "./routes/index.js";
import { hideRouter } from "./routes/hide.js";
import { extractRouter } from "./routes/extract.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(compression());
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        fontSrc: ["'self'", "https://fonts.gstatic.com"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", "data:"],
      },
    },
  })
);

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "../views"));

app.use(
  express.static(path.join(__dirname, "../public"), {
    maxAge: "1d",
  })
);

app.use("/", indexRouter);
app.use("/", hideRouter);
app.use("/", extractRouter);

const port = parseInt(process.env.PORT || "9000", 10);
const server = app.listen(port, "0.0.0.0");
server.on("error", (err) => {
  process.stderr.write(`Failed to start: ${err.message}\n`);
  process.exit(1);
});
