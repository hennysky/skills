#!/usr/bin/env node
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export async function checkForUpdate({ releasePath = new URL('../skill-release.json', import.meta.url) } = {}) {
  const release = JSON.parse(fs.readFileSync(releasePath, 'utf8'));
  return { status: 'local-only', installedVersion: release.version, availableVersion: null,
    source: 'local-release', checkedAt: null, noticeRequired: false, noticeText: null,
    reason: 'remote-updates-not-configured' };
}
export async function setUpdatePreference() {
  return { status: 'not-applicable', reason: 'remote-updates-not-configured' };
}
export function isMainModule() {
  return Boolean(process.argv[1]) && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}
if (isMainModule()) console.log(JSON.stringify(await checkForUpdate(), null, 2));
