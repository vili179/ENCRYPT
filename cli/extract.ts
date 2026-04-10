import { readFile } from "fs/promises";
import { revealMessage } from "../src/services/steganography.js";

const args = process.argv.slice(2);
if (args.length !== 2) {
  process.stderr.write("Usage: npx tsx cli/extract.ts <image> <password>\n");
  process.exit(1);
}

const [imagePath, password] = args;
const imageBuffer = await readFile(imagePath);
const message = await revealMessage(imageBuffer, password);
process.stdout.write(message + "\n");
