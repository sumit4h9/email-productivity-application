/* Fix lightningcss native binary location for environments where optional dependency postinstall didn't copy it.
 * Copies the platform-specific binary from its optional package into node_modules/lightningcss/
 */
const fs = require("fs");
const path = require("path");

function copyBin(srcPkg, filename) {
  const src = path.join("node_modules", srcPkg, filename);
  const destDir = path.join("node_modules", "lightningcss");
  const dest = path.join(destDir, filename);
  if (fs.existsSync(src)) {
    fs.mkdirSync(destDir, { recursive: true });
    try {
      fs.copyFileSync(src, dest);
      console.log(`[fix-lightningcss] Copied ${src} -> ${dest}`);
      return true;
    } catch (e) {
      console.warn(`[fix-lightningcss] Failed to copy: ${e.message}`);
    }
  }
  return false;
}

const mappings = [
  {
    pkg: "lightningcss-linux-x64-gnu",
    file: "lightningcss.linux-x64-gnu.node",
  },
  {
    pkg: "lightningcss-linux-x64-musl",
    file: "lightningcss.linux-x64-musl.node",
  },
  {
    pkg: "lightningcss-linux-arm64-gnu",
    file: "lightningcss.linux-arm64-gnu.node",
  },
  {
    pkg: "lightningcss-linux-arm-gnueabihf",
    file: "lightningcss.linux-arm-gnueabihf.node",
  },
  { pkg: "lightningcss-darwin-x64", file: "lightningcss.darwin-x64.node" },
  { pkg: "lightningcss-darwin-arm64", file: "lightningcss.darwin-arm64.node" },
  {
    pkg: "lightningcss-win32-x64-msvc",
    file: "lightningcss.win32-x64-msvc.node",
  },
  {
    pkg: "lightningcss-win32-arm64-msvc",
    file: "lightningcss.win32-arm64-msvc.node",
  },
  { pkg: "lightningcss-freebsd-x64", file: "lightningcss.freebsd-x64.node" },
];

let done = false;
for (const m of mappings) {
  done = copyBin(m.pkg, m.file) || done;
}

if (!done) {
  console.log(
    "[fix-lightningcss] No platform binary found to copy (may already be present)."
  );
}
