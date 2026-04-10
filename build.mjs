import { build } from "esbuild";

await build({
  entryPoints: [
    "public/ts/common.ts",
    "public/ts/hide.ts",
    "public/ts/extract.ts",
  ],
  bundle: true,
  outdir: "public/js",
  minify: true,
  format: "iife",
  target: "es2020",
});
