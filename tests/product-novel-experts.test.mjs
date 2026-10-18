import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const base = path.resolve('plugins/yijie-desktop-skills/experts');
const pm = path.join(base, 'product-management/skills/product-workbench');
const novel = path.join(base, 'novel-creator/skills/story-workbench');
const read = file => JSON.parse(readFileSync(file, 'utf8'));
const plan = () => read(path.join(pm, 'examples/plan.json'));
const story = () => read(path.join(novel, 'examples/story.json'));
const digest = file => createHash('sha256').update(readFileSync(file)).digest('hex');

function workspace(fn) {
  const dir = mkdtempSync(path.join(tmpdir(), 'yijie-product-novel-normal-'));
  try { fn(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}
function run(dir, type, input, output = 'v1', previous = null) {
  const file = path.join(dir, `input-${output}.json`);
  writeFileSync(file, JSON.stringify(input));
  const args = ['-B', path.join(type === 'pm' ? pm : novel, 'scripts', type === 'pm' ? 'product.py' : 'story.py'), '--input', file, '--out', path.join(dir, output)];
  if (type === 'pm') args.push('--sources', path.join(pm, 'examples/sources.json'));
  if (previous) args.push('--previous', path.join(dir, previous));
  return spawnSync('python3', args, { encoding: 'utf8' });
}
function pass(result) { assert.equal(result.status, 0, result.stderr); }
function verifyReceipt(dir) {
  for (const item of read(path.join(dir, 'receipt.json')).files) assert.equal(digest(path.join(dir, item.path)), item.sha256);
}

test('PM produces all six real documents, exact RICE, source snapshots and matching file receipts', () => workspace(dir => {
  pass(run(dir, 'pm', plan()));
  for (const kind of ['prd', 'roadmap', 'stakeholder', 'research', 'competitive', 'metrics']) assert.ok(readFileSync(path.join(dir, 'v1', `${kind}.md`), 'utf8').includes('S1'));
  const rice = read(path.join(dir, 'v1/rice.json'));
  assert.equal(rice.items[0].score, '80.0');
  assert.equal(rice.items[1].score, null);
  assert.deepEqual(rice.ranked_ids, ['export']);
  assert.deepEqual(rice.unranked_ids, ['unknown']);
  verifyReceipt(path.join(dir, 'v1'));
}));
test('PM treats explicit zero confidence/reach as known, while missing parameters remain unranked', () => workspace(dir => {
  const p = plan(); p.rice.items[0].confidence = 0; p.rice.items[1].reach = 0;
  pass(run(dir, 'pm', p));
  const result = read(path.join(dir, 'v1/rice.json'));
  assert.deepEqual(result.items.map(r => Number(r.score)), [0, 0]);
  assert.deepEqual(result.unranked_ids, []);
}));
test('PM requires consistent RICE period/unit and a positive known effort', () => workspace(dir => {
  for (const [key, value] of [['reach_period', '2027Q1'], ['effort_unit', '人周'], ['effort', 0], ['confidence', 80]]) {
    const p = plan(); p.rice.items[0][key] = value;
    assert.notEqual(run(dir, 'pm', p).status, 0);
    assert.equal(existsSync(path.join(dir, 'v1')), false);
  }
}));
test('PM rejects ordinary misquoted interview text and unknown source identity before writing', () => workspace(dir => {
  const p = plan(); p.documents.find(d => d.kind === 'research').quotes[0].text = '每周都能自动复制清单。';
  assert.notEqual(run(dir, 'pm', p).status, 0);
  assert.equal(existsSync(path.join(dir, 'v1')), false);
  const other = plan(); other.documents[0].source_ids = ['unprovided-interview'];
  assert.notEqual(run(dir, 'pm', other).status, 0);
}));
test('PM reprioritization writes a new version and preserves every old output', () => workspace(dir => {
  const p = plan(); pass(run(dir, 'pm', p));
  const old = read(path.join(dir, 'v1/receipt.json'));
  p.rice.items[0].effort = 4;
  pass(run(dir, 'pm', p, 'v2'));
  assert.equal(read(path.join(dir, 'v2/rice.json')).items[0].score, '40.0');
  for (const f of old.files) assert.equal(digest(path.join(dir, 'v1', f.path)), f.sha256);
  assert.notEqual(run(dir, 'pm', p, 'v1').status, 0);
  verifyReceipt(path.join(dir, 'v1'));
}));

test('story saves actual chapter and all four ledgers with file receipts', () => workspace(dir => {
  const input = story(); pass(run(dir, 'novel', input));
  for (const key of Object.keys(input.tracking)) assert.deepEqual(read(path.join(dir, 'v1/tracking', `${key}.json`)), input.tracking[key]);
  assert.ok(readFileSync(path.join(dir, 'v1/chapters/ch001.md'), 'utf8').includes(input.chapters[0].text));
  verifyReceipt(path.join(dir, 'v1'));
}));
test('story continuation reads previous receipt and retains original chapter bytes', () => workspace(dir => {
  const input = story(); pass(run(dir, 'novel', input));
  input.revision = 2; input.stage = 'continuation';
  input.chapters.push({ ...input.chapters[0], id: 'ch002', number: 2, title: '锁孔', text: '岚沿着干燥的楼梯走上去，钥匙在掌心发凉。' });
  input.tracking.timeline.push({ id: 't002', chapter_id: 'ch002', sequence: 2, time_label: '第二日晨', event: '走上楼梯', character_ids: ['lan'] });
  pass(run(dir, 'novel', input, 'v2', 'v1'));
  assert.equal(digest(path.join(dir, 'v1/chapters/ch001.md')), digest(path.join(dir, 'v2/chapters/ch001.md')));
  verifyReceipt(path.join(dir, 'v1')); verifyReceipt(path.join(dir, 'v2'));
}));
test('story setting edits produce impact and unresolved review list without changing old manuscripts', () => workspace(dir => {
  const input = story(); pass(run(dir, 'novel', input));
  input.revision = 2; input.stage = 'revision'; input.change_reason = '用户要求修改人物游泳能力，正文尚待联动';
  input.facts[0].text = '岚会游泳。';
  pass(run(dir, 'novel', input, 'v2', 'v1'));
  const impact = read(path.join(dir, 'v2/impact.json'));
  assert.deepEqual(impact.changed_facts, ['f_swim']);
  assert.deepEqual(impact.review_required_chapters, ['ch001']);
  assert.equal(read(path.join(dir, 'v2/receipt.json')).semantic_review, 'required');
  verifyReceipt(path.join(dir, 'v1'));
}));
test('story refuses chapters without user confirmation and incomplete Brief', () => workspace(dir => {
  const a = story(); a.bible_confirmed = false;
  assert.notEqual(run(dir, 'novel', a).status, 0);
  const b = story(); delete b.brief.pov;
  assert.notEqual(run(dir, 'novel', b).status, 0);
  assert.equal(existsSync(path.join(dir, 'v1')), false);
}));
test('story checks all normal chapter/character/fact relationships and resolution order', () => workspace(dir => {
  const mutations = [s => { s.chapters[0].pov = 'unknown'; }, s => { s.chapters[0].fact_ids = ['unestablished']; }, s => { s.tracking['character-state'] = []; }, s => { s.tracking['plot-tracker'][0].status = 'resolved'; }, s => { s.tracking.relationships.push({ id: 'r1', from: 'lan', to: 'unknown', description: '朋友', as_of_chapter: 'ch001' }); }];
  for (const mutate of mutations) {
    const s = story(); mutate(s);
    assert.notEqual(run(dir, 'novel', s).status, 0);
    assert.equal(existsSync(path.join(dir, 'v1')), false);
  }
}));
test('story revision requires exact project, next revision and preserves chapter IDs', () => workspace(dir => {
  const s = story(); pass(run(dir, 'novel', s));
  for (const mutate of [v => { v.project_id = 'different-project'; }, v => { v.revision = 4; }, v => { v.chapters = []; v.tracking.timeline = []; v.tracking['plot-tracker'] = []; v.tracking['character-state'][0].as_of_chapter = null; }]) {
    const v = story(); v.revision = 2; mutate(v);
    assert.notEqual(run(dir, 'novel', v, 'v2', 'v1').status, 0);
    assert.equal(existsSync(path.join(dir, 'v2')), false);
  }
  assert.notEqual(run(dir, 'novel', s, 'v1').status, 0);
  verifyReceipt(path.join(dir, 'v1'));
}));
test('story requires updated chapter timeline and rejects knowledge ahead of character state', () => workspace(dir => {
  const s = story(); s.tracking.timeline = [];
  assert.notEqual(run(dir, 'novel', s).status, 0);
  const next = story(); next.facts[0].established_chapter = 'ch001'; next.tracking['character-state'][0].as_of_chapter = null;
  assert.notEqual(run(dir, 'novel', next).status, 0);
  assert.equal(existsSync(path.join(dir, 'v1')), false);
}));
