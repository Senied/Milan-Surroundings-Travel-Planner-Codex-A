import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const [url, output] = process.argv.slice(2);
if (!url || !output) {
  throw new Error("Usage: node tools/print_guide.mjs <guide-url> <output.pdf>");
}

const browser = await chromium.launch({
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
});

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.emulateMedia({ media: "print", reducedMotion: "reduce" });
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    const images = [...document.images];
    images.forEach(image => { image.loading = "eager"; });
    await Promise.all(images.map(image => image.decode().catch(() => undefined)));
  });
  process.stdout.write("Guide loaded; creating PDF...\n");
  await page.pdf({
    path: output,
    format: "A4",
    preferCSSPageSize: true,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="width:100%;height:1px;font-size:0;color:transparent;">&nbsp;</div>',
    footerTemplate: `
      <div style="box-sizing:border-box;width:100%;padding:0 14mm 5mm;display:flex;justify-content:space-between;align-items:center;color:#6e6e73;font:9px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:.02em;">
        <span>Milan &amp; Surroundings · Travel Guide</span>
        <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
      </div>`,
    tagged: true,
    outline: true,
  });
  process.stdout.write("PDF created.\n");
} finally {
  await browser.close();
}
