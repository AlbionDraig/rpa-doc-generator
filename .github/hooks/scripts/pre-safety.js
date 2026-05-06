#!/usr/bin/env node
/**
 * PreToolUse safety hook.
 * Reads the tool invocation from stdin (JSON), checks for destructive patterns,
 * and asks for user confirmation if any are found.
 * Exit 0 (non-blocking) on all code paths — denial is via JSON output only.
 */

const chunks = [];
process.stdin.on('data', chunk => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const payload = JSON.stringify(data.toolInput || {}).toLowerCase();

    const dangerous = [
      'rm -rf',
      'git push --force',
      'git push -f',
      'git reset --hard',
      'drop table',
      'drop database',
      'drop schema',
      'truncate table',
      '--no-verify',
      'format c:',
      'del /f /s /q',
      'remove-item -recurse -force',
    ];

    const found = dangerous.find(p => payload.includes(p));
    if (found) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'ask',
          permissionDecisionReason:
            `Operación potencialmente destructiva detectada: "${found}". Confirma antes de continuar.`,
        },
      }));
    }
  } catch (_) {
    // Non-blocking: parse errors do not interrupt the agent
  }
});
