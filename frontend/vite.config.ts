import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import {resolve, dirname, join} from "node:path";
import {fileURLToPath} from "node:url";
import fs from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));

function copyDirRecursive(src: string, dest: string) {
  fs.mkdirSync(dest, {recursive: true});
  for (const entry of fs.readdirSync(src, {withFileTypes: true})) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else if (entry.name.endsWith(".json") || entry.name.endsWith(".png")) {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function dataLoaderPlugin() {
  return {
    name: "data-loader",
    configureServer(server: any) {
      server.middlewares.use("/data", (req: any, res: any, next: any) => {
        const filePath = resolve(__dirname, "..", "data", "output", req.url.replace(/^\//, ""));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const contentType = filePath.endsWith(".png") ? "image/png" : "application/json";
          res.setHeader("Content-Type", contentType);
          fs.createReadStream(filePath).pipe(res);
        } else {
          next();
        }
      });
    },
    writeBundle() {
      const srcDir = resolve(__dirname, "..", "data", "output");
      const destDir = resolve(__dirname, "dist", "data");
      if (fs.existsSync(srcDir)) {
        copyDirRecursive(srcDir, destDir);
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), dataLoaderPlugin()],
  base: process.env.BASE_URL || "/",
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          recharts: ["recharts"],
        },
      },
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
});
