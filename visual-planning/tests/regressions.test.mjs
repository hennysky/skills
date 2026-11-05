import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from '../scripts/planning-page.mjs';
import {parseExplainer} from '../explainer/parse.mjs';
import {ChromeVisualBrowser,findChrome} from '../bin/visual-check.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');

test('repeated ordinary table labels get distinct stable identities',()=>{
 const text='# 方案\n\n保留每条依据。\n\n## 依据\n\n| 类型 | 说明 |\n| --- | --- |\n| 当前事实 | 第一条 |\n| 当前事实 | 第二条 |\n';
 const {document}=parseExplainer(text,{output:'plan.html'}),rows=document.panels[0].blocks[0].rows;
 assert.equal(new Set(rows.map(r=>r.id)).size,2);
 assert.deepEqual(rows.map(r=>r.label),['当前事实','当前事实']);
});

test('source checklist completion survives parsing',()=>{
 const {document}=parseExplainer('# 方案\n\n记录已核实状态。\n\n## 待办\n\n- [x] 已确认。\n- [ ] 待执行。\n',{output:'plan.html'});
 assert.deepEqual(document.panels[0].blocks[0].checked,[true,false]);
});

test('narrow expanded diagram initially fits all nodes and keeps controls reachable',async(t)=>{
 const chrome=findChrome();
 if(!chrome){t.skip('Chrome unavailable; browser regression not verified');return;}
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'visual-narrow-regression-'));
 const b=new ChromeVisualBrowser(chrome);
 async function e(expression,session){const r=await b.cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
 try{
  const out=path.join(tmp,'delivery');build({plan:path.join(root,'tests/fixtures/csv-import.plan.md'),diagram:path.join(root,'tests/fixtures/csv-import.workflow.json'),out});
  const s=await b.sessionPromise;
  await b.cdp.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false},s);
  const loaded=b.cdp.waitFor('Page.loadEventFired',s);loaded.catch(()=>{});
  await b.cdp.send('Page.navigate',{url:pathToFileURL(path.join(out,'规划页.html')).href},s);await loaded;
  await e('document.fonts.ready',s);
  assert.deepEqual(await e('[...document.querySelectorAll("input[type=checkbox]")].map(x=>x.checked)',s),[true,false],'Authored completion must reach the actual page');
  await e('document.querySelector("[data-open-diagram]").click()',s);
  let ready=false;
  for(let i=0;i<60;i++){if(await e('!!document.querySelector("#diagram-dialog").dataset.nativeFocus',s)){ready=true;break;}await new Promise(r=>setTimeout(r,50));}
  assert.ok(ready,'Expanded native viewer did not settle');
  const tree=await b.cdp.send('Page.getFrameTree',{},s),targets=await b.cdp.send('Target.getTargets');
  const target=targets.targetInfos.find(x=>x.type==='iframe'&&x.parentId===tree.frameTree.frame.id&&x.url.startsWith('about:srcdoc'));
  assert.ok(target,'Sandboxed native frame not found');
  const attached=await b.cdp.send('Target.attachToTarget',{targetId:target.targetId,flatten:true});const ss=attached.sessionId;
  await b.cdp.send('Runtime.enable',{},ss);
  const measure=`(()=>{const c=document.querySelector('.diagram-container'),r=c.getBoundingClientRect(),visible=e=>e.getBoundingClientRect().width>0,rect=e=>{let z=e.getBoundingClientRect();return{id:e.dataset.nodeId||e.ariaLabel,left:z.left,right:z.right,top:z.top,bottom:z.bottom}};return{width:innerWidth,nodes:[...c.querySelectorAll('svg [data-node-id]')].filter(visible).map(rect).filter(n=>n.left<r.left-1||n.right>r.right+1||n.top<r.top-1||n.bottom>r.bottom+1),controls:[...document.querySelectorAll('.diagram-nav button,.toolbar button')].filter(visible).map(rect).filter(n=>n.left < -1||n.right>innerWidth+1)}})()`;
  const metrics=await e(measure,ss);
  assert.deepEqual(metrics.nodes,[],'Initial overview clips graph nodes');
  assert.deepEqual(metrics.controls,[],'Interactive controls extend beyond the frame');
  const before=await e('VisualPlan.view.state().scale',ss);await e('document.querySelector("[data-view=in]").click()',ss);const after=await e('VisualPlan.view.state().scale',ss);assert.ok(after>before,'Zoom remains interactive');
  await e('document.querySelector("[data-view=reset]").click()',ss);
  const reset=await e(measure,ss);assert.deepEqual(reset.nodes,[],'Reset must restore the hosted overview');

 }finally{await b.close();fs.rmSync(tmp,{recursive:true,force:true});}
});
