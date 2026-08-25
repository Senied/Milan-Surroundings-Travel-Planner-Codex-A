import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputRoot = join(projectRoot, "dist");
const clientRoot = join(outputRoot, "client");
const serverRoot = join(outputRoot, "server");
const publicEntries = [
  ".nojekyll",
  "index.html",
  "styles.css",
  "app.js",
  "favicon.svg",
  "assets",
  "guide",
  "previous",
  "releases",
];

if (!clientRoot.startsWith(`${outputRoot}${sep}`)) {
  throw new Error("Refusing to build outside the project distribution folder.");
}

await rm(clientRoot, { recursive: true, force: true });
await mkdir(clientRoot, { recursive: true });
await rm(serverRoot, { recursive: true, force: true });
await mkdir(serverRoot, { recursive: true });

for (const entry of publicEntries) {
  await cp(join(projectRoot, entry), join(clientRoot, entry), {
    recursive: true,
    force: true,
  });
}

// The downloadable package is supplied separately; the site keeps only guide editions.
await rm(
  join(
    clientRoot,
    "releases",
    "Milan_Surroundings_Travel_Guide_2026_v1_2_bundle.zip",
  ),
  { force: true },
);

await cp(
  join(projectRoot, "worker", "index.js"),
  join(serverRoot, "index.js"),
);

console.log(`Prepared ${publicEntries.length} public entries for hosting.`);
