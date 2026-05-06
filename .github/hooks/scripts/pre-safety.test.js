#!/usr/bin/env node
/**
 * Smoke tests for pre-safety.js hook.
 * Run with: node .github/hooks/scripts/pre-safety.test.js
 * Exit 0 = all tests passed. Exit 1 = failure.
 */

const { execSync } = require('child_process');
const path = require('path');

const HOOK = path.join(__dirname, 'pre-safety.js');
let passed = 0;
let failed = 0;

/**
 * Runs the hook with the given payload and returns the parsed stdout.
 * @param {object} payload - Tool invocation payload.
 * @returns {object|null} Parsed JSON output, or null if empty.
 */
function runHook(payload) {
  const input = JSON.stringify(payload);
  const stdout = execSync(`node "${HOOK}"`, { input, encoding: 'utf8' });
  return stdout.trim() ? JSON.parse(stdout) : null;
}

/**
 * Asserts a condition and reports the result.
 * @param {string} name - Test name.
 * @param {boolean} condition - Expected to be true.
 */
function assert(name, condition) {
  if (condition) {
    console.log(`  ✓ ${name}`);
    passed++;
  } else {
    console.error(`  ✗ ${name}`);
    failed++;
  }
}

console.log('\npre-safety.js hook — smoke tests\n');

// --- Safe payloads (should return null / no output) ---
console.log('Safe payloads (expect: no output)');

assert(
  'normal shell command passes through',
  runHook({ toolInput: { command: 'ls -la' } }) === null,
);
assert(
  'git status passes through',
  runHook({ toolInput: { command: 'git status' } }) === null,
);
assert(
  'empty toolInput passes through',
  runHook({ toolInput: {} }) === null,
);
assert(
  'missing toolInput passes through',
  runHook({}) === null,
);

// --- Dangerous payloads (should return permissionDecision: "ask") ---
console.log('\nDangerous payloads (expect: permissionDecision = "ask")');

const dangerousCases = [
  ['rm -rf', { command: 'rm -rf /tmp/test' }],
  ['git push --force', { command: 'git push --force origin main' }],
  ['git push -f shorthand', { command: 'git push -f' }],
  ['git reset --hard', { command: 'git reset --hard HEAD~1' }],
  ['DROP TABLE', { query: 'DROP TABLE users' }],
  ['DROP DATABASE', { query: 'DROP DATABASE atlas' }],
  ['TRUNCATE TABLE', { query: 'TRUNCATE TABLE transactions' }],
  ['--no-verify', { command: 'git commit --no-verify -m "skip"' }],
  ['del /f /s /q (windows)', { command: 'del /f /s /q C:\\data' }],
  ['Remove-Item -Recurse -Force (powershell)', { command: 'Remove-Item -Recurse -Force C:\\data' }],
];

for (const [label, toolInput] of dangerousCases) {
  const result = runHook({ toolInput });
  assert(
    `blocks: ${label}`,
    result?.hookSpecificOutput?.permissionDecision === 'ask',
  );
}

// --- Malformed input (should not throw) ---
console.log('\nMalformed input (expect: no crash)');

try {
  execSync(`echo "not-json" | node "${HOOK}"`, { encoding: 'utf8' });
  assert('malformed JSON does not crash hook', true);
} catch (_) {
  assert('malformed JSON does not crash hook', false);
}

// --- Summary ---
console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
