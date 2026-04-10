import { readFile, writeFile } from "fs/promises";
import { hideMessage } from "../src/services/steganography.js";

const args = process.argv.slice(2);
if (args.length !== 4) {
  process.stderr.write(
    "Usage: npx tsx cli/hide.ts <input> <message> <password> <output>\n"
  );
  process.exit(1);
}

const [inputPath, message, password, outputPath] = args;
const imageBuffer = await readFile(inputPath);
const result = await hideMessage(imageBuffer, message, password);
await writeFile(outputPath, result.buffer);
process.stdout.write(
  `Hidden ${result.bitsUsed} bits in ${result.width}x${result.height} image -> ${outputPath}\n`
);
