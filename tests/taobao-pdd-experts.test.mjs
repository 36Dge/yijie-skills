import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const root = path.resolve('plugins/yijie-desktop-skills/experts');
const packages = [
  ['tb-tm-ops-expert', 'taobao-workbench'],
  ['pdd-ops-expert', 'pdd-workbench'],
];
for (const [id, runtime] of packages) {
  test(`${id}: normal data, real CSV/XLSX, exact finance, gaps, score systems and versioned output`, () => {
    const result = spawnSync('python3', ['-B', 'tests/support/taobao-pdd-diagnose.py', path.join(root, id, 'skills', runtime)], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.match(result.stderr, /Ran 19 tests/);
  });
}
test('two independently installed packages use the same reviewed calculator without cross-package imports', () => {
  for (const file of ['diagnose.py', 'tableio.py']) {
    const files = packages.map(([id, runtime]) => readFileSync(path.join(root, id, 'skills', runtime, 'scripts', file)));
    assert.deepEqual(files[0], files[1]);
  }
  const profiles = packages.map(([id, runtime]) => JSON.parse(readFileSync(path.join(root, id, 'skills', runtime, 'profile.json'))));
  assert.deepEqual(profiles.map(p => p.platforms), [['taobao', 'tmall'], ['pdd']]);
});

for (const [id, runtime] of packages) {
  test(`${id}@0.1.1: full normal input regression and visible null/snapshot repair`, () => {
    const folder = path.join(root, id, 'skills', `${runtime}-v011`);
    for (const [script, count] of [['taobao-pdd-diagnose.py', 19], ['taobao-pdd-report-repair.py', 3]]) {
      const result = spawnSync('python3', ['-B', `tests/support/${script}`, folder], { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stdout + result.stderr);
      assert.ok(result.stderr.includes(`Ran ${count} tests`));
    }
  });
}
test('0.1.1 calculator remains identical across the two standalone expert packages', () => {
  for (const file of ['diagnose.py', 'tableio.py']) {
    assert.deepEqual(...packages.map(([id, runtime]) => readFileSync(path.join(root, id, 'skills', `${runtime}-v011`, 'scripts', file))));
  }
});

for (const [id, runtime] of packages) {
  test(`${id}@0.1.2: responsive presentation preserves full finance, source and null regressions`, () => {
    const folder = path.join(root, id, 'versions', '0.1.2', runtime);
    for (const [script, count] of [['taobao-pdd-diagnose.py', 19], ['taobao-pdd-report-repair.py', 3]]) {
      const args = ['-B', `tests/support/${script}`, folder];
      if (script === 'taobao-pdd-report-repair.py') args.push('0.1.2');
      const result = spawnSync('python3', args, { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stdout + result.stderr);
      assert.ok(result.stderr.includes(`Ran ${count} tests`));
    }
  });
}
test('0.1.2 report and table readers remain identical in both standalone expert packages', () => {
  for (const file of ['diagnose.py', 'tableio.py']) {
    assert.deepEqual(...packages.map(([id, runtime]) => readFileSync(path.join(root, id, 'versions', '0.1.2', runtime, 'scripts', file))));
  }
});

for (const [id, runtime] of packages) {
  test(`${id}@0.1.3: responsive presentation preserves full finance, source and null regressions`, () => {
    const folder = path.join(root, id, 'versions', '0.1.3', runtime);
    for (const [script, count] of [['taobao-pdd-diagnose.py', 19], ['taobao-pdd-report-repair.py', 3]]) {
      const args = ['-B', `tests/support/${script}`, folder];
      if (script === 'taobao-pdd-report-repair.py') args.push('0.1.3');
      const result = spawnSync('python3', args, { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stdout + result.stderr);
      assert.ok(result.stderr.includes(`Ran ${count} tests`));
    }
  });
}
test('0.1.3 report and table readers remain identical in both standalone expert packages', () => {
  for (const file of ['diagnose.py', 'tableio.py']) {
    assert.deepEqual(...packages.map(([id, runtime]) => readFileSync(path.join(root, id, 'versions', '0.1.3', runtime, 'scripts', file))));
  }
});
