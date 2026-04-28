
import assert from "assert";

// Mock log function
const logs = [];
function log(msg) {
  logs.push(msg);
}

// Mock state
let MODEL_CODE = "gemini-3-flash-preview";
let MODEL_PROVIDER = "google-gemini-cli";
const FALLBACK_MODEL_CODE = "gemini-3-pro-preview";
const FALLBACK_MODEL_PROVIDER = "google-gemini-cli";

function simulateRunCycle(taskInput) {
  let task = taskInput;
  let currentModelCode = MODEL_CODE;
  let currentModelProvider = MODEL_PROVIDER;

  // Check if this is a heavy task
  if (task.startsWith("[HEAVY]")) {
    log(`Heavy task detected. Using fallback model: ${FALLBACK_MODEL_CODE || "gemini-3-pro-preview"}`);
    if (FALLBACK_MODEL_CODE) {
      currentModelCode = FALLBACK_MODEL_CODE;
      currentModelProvider = FALLBACK_MODEL_PROVIDER || "google-gemini-cli";
    } else {
      currentModelCode = "gemini-3-pro-preview";
      currentModelProvider = "google-gemini-cli";
    }
    task = task.replace("[HEAVY]", "").trim();
  }

  return { task, currentModelCode, currentModelProvider };
}

// Test 1: Normal task
const res1 = simulateRunCycle("Normal task");
assert.strictEqual(res1.task, "Normal task");
assert.strictEqual(res1.currentModelCode, "gemini-3-flash-preview");
console.log("✓ Normal task uses default model");

// Test 2: [HEAVY] task
const res2 = simulateRunCycle("[HEAVY] Complex task");
assert.strictEqual(res2.task, "Complex task");
assert.strictEqual(res2.currentModelCode, "gemini-3-pro-preview");
assert.ok(logs.some(l => l.includes("Heavy task detected")));
console.log("✓ [HEAVY] task uses fallback model");

// Test 3: [HEAVY] task without fallback configured
const oldFallback = MODEL_CODE;
MODEL_CODE = "flash";
const res3 = simulateRunCycle("[HEAVY] Another task");
assert.strictEqual(res3.task, "Another task");
assert.strictEqual(res3.currentModelCode, "gemini-3-pro-preview"); // defaults to pro-preview
console.log("✓ [HEAVY] task defaults to pro-preview if no fallback configured");

console.log("\nAll heavy task tests passed!");
