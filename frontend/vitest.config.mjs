import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  oxc: {
    include: /.*\.[jt]sx?$/,
    lang: "jsx",
    jsx: {
      runtime: "automatic",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./tests/setup.js",
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "./coverage",
    },
  },
});
