import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const KB = 1024;
const budgets = {
  entryJs: { raw: 230 * KB, gzip: 90 * KB },
  asyncJs: { raw: 200 * KB, gzip: 70 * KB },
  entryCss: { raw: 75 * KB, gzip: 12 * KB },
};
const forbiddenInitialSources = new Set([
  "node_modules/jszip/dist/jszip.min.js",
  "node_modules/qrcode/lib/browser.js",
  "src/components/billing/RechargeModal.vue",
]);
const forbiddenInitialNames = new Set(["StrategyReviewShell"]);
const deferredStrategyRoutes = [
  "src/views/generator/outfit/OutfitView.vue",
  "src/views/generator/product-image/ProductImageView.vue",
  "src/views/generator/product-suite/ProductSuiteView.vue",
];
const root = process.cwd();
const dist = join(root, "dist");
const manifest = JSON.parse(
  readFileSync(join(dist, ".vite", "manifest.json"), "utf8"),
);
const entry = Object.entries(manifest).find(([, value]) => value.isEntry);

if (!entry) throw new Error("Vite manifest 中未找到入口 chunk");

function staticClosure(key, result = new Set()) {
  if (result.has(key)) return result;
  result.add(key);
  for (const dependency of manifest[key]?.imports || []) staticClosure(dependency, result);
  return result;
}

function sizeOf(file) {
  const content = readFileSync(join(dist, file));
  return { raw: content.byteLength, gzip: gzipSync(content).byteLength };
}

function formatSize(bytes) {
  return `${(bytes / KB).toFixed(2)} KB`;
}

function enforce(label, file, budget, violations, { print = true } = {}) {
  const size = sizeOf(file);
  if (print) {
    console.log(`${label}: ${file} raw=${formatSize(size.raw)} gzip=${formatSize(size.gzip)}`);
  }
  if (size.raw > budget.raw) {
    violations.push(`${file} 原始体积 ${formatSize(size.raw)} > ${formatSize(budget.raw)}`);
  }
  if (size.gzip > budget.gzip) {
    violations.push(`${file} gzip 体积 ${formatSize(size.gzip)} > ${formatSize(budget.gzip)}`);
  }
  return size;
}

const [entryKey, entryChunk] = entry;
const initialKeys = staticClosure(entryKey);
const initialFiles = new Set([...initialKeys].map((key) => manifest[key]?.file).filter(Boolean));
const violations = [];

enforce("entry-js", entryChunk.file, budgets.entryJs, violations);
for (const cssFile of entryChunk.css || []) {
  enforce("entry-css", cssFile, budgets.entryCss, violations);
}

const asyncChunks = [];
for (const file of readdirSync(join(dist, "assets"))) {
  const relative = `assets/${file}`;
  if (!file.endsWith(".js") || initialFiles.has(relative)) continue;
  asyncChunks.push({
    file: relative,
    ...enforce("async-js", relative, budgets.asyncJs, violations, { print: false }),
  });
}
for (const chunk of asyncChunks.sort((left, right) => right.raw - left.raw).slice(0, 10)) {
  console.log(
    `async-js: ${chunk.file} raw=${formatSize(chunk.raw)} gzip=${formatSize(chunk.gzip)}`,
  );
}

for (const key of initialKeys) {
  const chunk = manifest[key];
  if (forbiddenInitialSources.has(key) || forbiddenInitialNames.has(chunk?.name)) {
    violations.push(`${key} 不应进入首屏静态依赖`);
  }
}

for (const source of forbiddenInitialSources) {
  if (!manifest[source]?.isDynamicEntry) {
    violations.push(`${source} 必须保持动态入口`);
  }
}

for (const route of deferredStrategyRoutes) {
  const routeImports = staticClosure(route);
  const eagerlyLoadedStrategy = [...routeImports].find(
    (key) => manifest[key]?.name === "StrategyReviewShell",
  );
  if (eagerlyLoadedStrategy) {
    violations.push(`${route} 不应静态加载 StrategyReviewShell`);
  }
}

const totalInitial = [...initialFiles].reduce(
  (sum, file) => sum + statSync(join(dist, file)).size,
  0,
);
console.log(`initial-static-total: ${formatSize(totalInitial)}`);

if (violations.length) {
  console.error("\nBundle budget violations:");
  for (const violation of violations) console.error(`- ${violation}`);
  process.exitCode = 1;
} else {
  console.log("bundle budgets passed");
}
