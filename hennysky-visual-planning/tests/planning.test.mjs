import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { compilePlan, build, check } from '../scripts/planning-page.mjs';
import { checkForUpdate } from '../scripts/check-update.mjs';
import { startDeliveryUpdateCheck } from '../bin/delivery-update.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const markdown='# 本地规划\n\n将导入分为校验与汇总两步。\n\n## 目标\n\n完整正文保留这个唯一标记：canonical-full-content。\n\n## 实施\n\n```bash\n## code heading is literal\nnode example.mjs\n```\n\n- [ ] T1 校验输入。\n- [x] T2 已确认格式。\n';

test('canonical plan retains complete paragraphs, code and checklist while gaining navigation',()=>{
 const {candidate,sections}=compilePlan(markdown,'workflow');
 assert.equal(sections.length,2);
 assert.ok(candidate.includes('canonical-full-content'));
 assert.ok(candidate.includes('## code heading is literal'));
 assert.ok(candidate.includes('- [x] T2 已确认格式。'));
 assert.match(candidate,/\[目标\]\(block:section-1\)/);
 assert.match(candidate,/@diagram workflow id=planning-flow source=diagram.json/);
});

test('unsupported structure and missing tasks fail instead of silently dropping implementation detail',()=>{
 assert.throws(()=>compilePlan(markdown.replace('## 实施','### 实施'),'workflow'),/level-two/);
 assert.throws(()=>compilePlan('# X\n\nA\n\n## B\n\nC','workflow'),/checklist/);
 assert.throws(()=>compilePlan(markdown+'\n```bash','workflow'),/Unclosed/);
});

test('independent local release never calls a remote updater',async()=>{
 let called=0;const original=globalThis.fetch;globalThis.fetch=()=>{called++;throw Error('Network forbidden');};
 try {assert.equal((await checkForUpdate()).status,'local-only');assert.equal((await startDeliveryUpdateCheck()).installedVersion,'1.1.3');assert.equal(called,0);}
 finally{globalThis.fetch=original;}
});

test('full planning delivery detects changes to DSH, diagram, candidate and HTML',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'visual-plan-test-'));
 try {
  const plan=path.join(dir,'plan.md');fs.writeFileSync(plan,markdown);
  const out=path.join(dir,'result');
  const r=build({plan,diagram:path.join(root,'docs/planning-flow.workflow.json'),out});
  assert.equal(r.status,'passed');assert.equal(fs.readFileSync(r.markdown,'utf8'),markdown);
  assert.throws(()=>build({plan,diagram:path.join(root,'docs/planning-flow.workflow.json'),out}),/not empty/);
  for(const file of ['DSH-实施计划.md','diagram.json','candidate.visualplan.md','规划页.html']) {
   const full=path.join(out,file),original=fs.readFileSync(full);fs.appendFileSync(full,'\nchanged');
   assert.throws(()=>check({out}),/Content changed/);fs.writeFileSync(full,original);
  }
  assert.equal(check({out}).status,'passed');
 } finally{fs.rmSync(dir,{recursive:true,force:true});}
});

test('the whole Skill can package and run after copying away from the project',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'visual-skill-portable-'));
 try{
  const install=path.join(dir,'hennysky-visual-planning');
  const pack=spawnSync('python3',[path.join(root,'scripts/package_skill.py'),'--out',path.join(dir,'dist'),'--install',install],{encoding:'utf8'});
  assert.equal(pack.status,0,pack.stderr);assert.ok(fs.existsSync(path.join(install,'renderers/shared/generated-validators.mjs')));
  const r=spawnSync(process.execPath,[path.join(install,'bin/visualplan.mjs'),'doctor'],{encoding:'utf8',cwd:dir});
  assert.equal(r.status,0,r.stdout+r.stderr);assert.match(r.stdout,/is ready/);
  const plan=path.join(dir,'source.md');fs.writeFileSync(plan,markdown);
  const b=spawnSync(process.execPath,[path.join(install,'scripts/planning-page.mjs'),'build','--plan',plan,'--diagram',path.join(install,'docs/planning-flow.workflow.json'),'--out',path.join(dir,'delivery')],{encoding:'utf8',cwd:dir});
  assert.equal(b.status,0,b.stdout+b.stderr);
  assert.ok(!fs.existsSync(path.join(install,'node_modules')));
  const again=spawnSync('python3',[path.join(root,'scripts/package_skill.py'),'--out',path.join(dir,'dist'),'--install',install],{encoding:'utf8'});
  assert.notEqual(again.status,0);assert.match(again.stderr,/overwrite/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});


test('independent project release identities stay in one namespace',async()=>{
 const {checkReleaseIdentity}=await import('../scripts/release-identity.mjs');
 assert.deepEqual(checkReleaseIdentity(),{name:'hennysky-visual-planning',version:'1.1.3',status:'passed'});
});

test('packaged chart engine renders synthetic pie and bar data without a network',async()=>{
 const {compileExplainerChart}=await import('../explainer/charts.mjs');
 for(const code of ['pie\n  "A": 2\n  "B": 3','xychart-beta\n  x-axis ["A", "B"]\n  y-axis "items" 0 --> 5\n  bar "Synthetic" [2, 3]']) {
  const result=compileExplainerChart(code);assert.equal(result.error,undefined);assert.match(result.svg,/<svg/);assert.ok(result.width>0&&result.height>0);
 }
});
