import { build } from "esbuild";
import { writeFileSync } from "node:fs";
import { generateProfiles } from "./gen-profiles.mjs";
generateProfiles();
const out = "no.berland.decksync.sdPlugin/bin";
// ws (brukt av SDK-en) er CommonJS og kaller require("events"); i en ESM-bundle finnes ikke require,
// så vi lager en med createRequire. Uten dette krasjer pluginen ved oppstart med exit-kode 1.
const banner = `import { createRequire } from "node:module"; const require = createRequire(import.meta.url);`;
await build({ entryPoints: ["src/plugin.ts"], bundle: true, platform: "node", format: "esm", target: "node20", outfile: `${out}/plugin.js`, minify: false, banner: { js: banner } });
writeFileSync(`${out}/package.json`, `{ "type": "module" }`);
console.log("built");
