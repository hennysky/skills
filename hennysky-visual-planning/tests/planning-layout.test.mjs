import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from '../scripts/planning-page.mjs';
import {parseExplainer} from '../explainer/parse.mjs';
import {renderExplainer} from '../explainer/render.mjs';
import {ChromeVisualBrowser,findChrome} from '../bin/visual-check.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');

test('ordinary explainers retain their board layout',()=>{
 const {document}=parseExplainer('# Plain explainer\n\nA complete answer.\n\n## Evidence\n\nThe supporting text.\n',{output:'plain.html'});
 const html=renderExplainer(document);
 assert.match(html,/data-layout="board"/);
 assert.ok(!html.includes('<aside class="planning-sidebar">'));
 assert.ok(html.includes('The supporting text.'));
});

test('planning layout avoids stretched cards, keeps mobile navigation compact and preserves reading state',async(t)=>{
 const chrome=findChrome();if(!chrome){t.skip('Chrome unavailable');return;}
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'hennysky-visual-planning-layout-'));
 const browser=new ChromeVisualBrowser(chrome);
 const evaluate=async expression=>{
  const result=await browser.cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},await browser.sessionPromise);
  if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value;
 };
 try{
  const source=fs.readFileSync(path.join(root,'tests/fixtures/csv-import.plan.md'),'utf8')+'\n## Wide table\n\n| A | B | C | D | E | F |\n| --- | --- | --- | --- | --- | --- |\n| one | two | three | four | five | six |\n'+Array.from({length:12},(_,i)=>`\n## Full chapter ${i}\n\nFull preserved paragraph ${i}.\n`).join('');
  const plan=path.join(dir,'source.md');fs.writeFileSync(plan,source);const out=path.join(dir,'delivery');
  build({plan,diagram:path.join(root,'tests/fixtures/csv-import.workflow.json'),out});
  const session=await browser.sessionPromise;
  const navigate=async()=>{const loaded=browser.cdp.waitFor('Page.loadEventFired',session);loaded.catch(()=>{});await browser.cdp.send('Page.navigate',{url:pathToFileURL(path.join(out,'规划页.html')).href},session);await loaded;await evaluate('document.fonts.ready');};
  await browser.cdp.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false},session);await navigate();
  const desktop=await evaluate(`(()=>{const nav=document.querySelector('.planning-sidebar').getBoundingClientRect(),main=document.querySelector('#board').getBoundingClientRect();return{side:nav.right<main.left,answer:document.querySelector('#answer').getBoundingClientRect().height,progress:document.querySelector('[data-plan-progress]').textContent,sections:document.querySelectorAll('.board>.panel').length,scroll:document.documentElement.scrollWidth,width:innerWidth}})()`);
  assert.equal(await evaluate(`[...document.querySelectorAll(".panel-id")].every(x=>parseFloat(getComputedStyle(x).fontSize)>=10)`),true);
  assert.equal(desktop.side,true);assert.ok(desktop.answer<240,'Conclusion must not stretch to the height of a long contents list');assert.equal(desktop.progress,'1 / 2');assert.equal(desktop.sections,17);assert.equal(desktop.scroll,desktop.width);
  await evaluate(`document.querySelectorAll('.checklist input')[1].click()`);assert.equal(await evaluate(`document.querySelector('[data-plan-progress]').textContent`),'2 / 2');
  await navigate();assert.deepEqual(await evaluate(`[...document.querySelectorAll('.checklist input')].map(x=>x.checked)`),[true,true]);
  await browser.cdp.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false},session);
  await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');
  const mobile=await evaluate(`(()=>{const table=document.querySelector('.table-scroll'),svg=document.querySelector('.diagram-preview>svg');return{open:document.querySelector('.planning-contents').open,scroll:document.documentElement.scrollWidth,width:innerWidth,tableScroll:table.scrollWidth>table.clientWidth,tableFits:table.getBoundingClientRect().right<=innerWidth,graphScroll:svg.getBoundingClientRect().width>svg.parentElement.clientWidth}})()`);
  await evaluate(`dispatchEvent(new Event('beforeprint'))`);assert.equal(await evaluate(`document.querySelector('.planning-contents').open`),true);await evaluate(`dispatchEvent(new Event('afterprint'))`);
  assert.equal(mobile.open,false);assert.equal(mobile.scroll,mobile.width);assert.equal(mobile.tableScroll,true);assert.equal(mobile.tableFits,true);assert.equal(mobile.graphScroll,true);
  await evaluate(`document.querySelector('.planning-contents summary').click()`);assert.equal(await evaluate(`document.querySelector('.planning-contents').open`),true);
  await evaluate(`document.querySelector('.planning-contents a[href="#section-15"]').click()`);assert.equal(await evaluate('location.hash'),'#section-15');assert.equal(await evaluate(`document.querySelector('.planning-contents').open`),false);
  assert.equal(await evaluate(`document.querySelector('#section-15').textContent.includes('Full preserved paragraph 11.')`),true);
  await evaluate(`document.querySelector('#section-15 a[href="#planning-nav"]').click()`);assert.equal(await evaluate(`document.querySelector('.planning-contents').open`),true);
  await evaluate(`scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'});dispatchEvent(new Event('scroll'));new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));`);
  assert.equal(await evaluate(`document.querySelector('.planning-contents a[aria-current]').hash`),'#section-15');
  // A mobile export expands contents and must still include the final chapter and live ticks.
  const exported = await evaluate(`(async()=>{
    document.querySelector('.planning-contents').open=false;
    const OriginalImage=window.Image;let captured='';
    window.Image=class extends OriginalImage {set src(value){captured=value;super.src=value;}get src(){return super.src;}};
    let bitmap;try{bitmap=await createImageBitmap(await VisualPlanExplainer.pageImage('png'));}finally{window.Image=OriginalImage;}
    const xml=new DOMParser().parseFromString(decodeURIComponent(captured.split(',').slice(1).join(',')),'image/svg+xml');
    const exportedRoot=document.importNode(xml.querySelector('foreignObject>html'),true);
    const holder=document.createElement('div');holder.style.cssText='position:fixed;left:-100000px;top:0;width:390px;visibility:hidden';holder.attachShadow({mode:'open'}).append(exportedRoot);document.body.append(holder);
    try {return {height:Number(xml.documentElement.getAttribute('height')),contentHeight:exportedRoot.querySelector('.shell').getBoundingClientRect().height,complete:exportedRoot.querySelector('#section-15').textContent.includes('Full preserved paragraph 11.'),checked:[...exportedRoot.querySelectorAll('.checklist input')].map(x=>x.hasAttribute('checked')),width:bitmap.width};}
    finally{holder.remove();bitmap.close();}
  })()`);
  assert.ok(exported.height>=exported.contentHeight,'Expanded mobile contents must not truncate the bottom of the exported page');assert.equal(exported.complete,true);assert.deepEqual(exported.checked,[true,true]);assert.ok(exported.width>=390);
  // Theme settles to readable controls as well as the page surface.
  await evaluate(`document.querySelector('[data-theme-choice="dark"]').click()`);
  assert.equal(await evaluate(`new Promise(resolve=>{const deadline=performance.now()+1500;const check=()=>{if(getComputedStyle(document.querySelector('[data-style-toggle]')).backgroundColor==='rgb(24, 37, 30)')resolve(true);else if(performance.now()>deadline)resolve(false);else requestAnimationFrame(check);};check();})`),true);
  assert.notEqual(await evaluate(`getComputedStyle(document.querySelector('.answer-id')).color`),'rgb(12, 13, 16)');
  // Rendering cannot borrow a saved style from ordinary explainer pages.
  await evaluate(`localStorage.setItem('visualplan-explainer-style','product')`);await navigate();assert.equal(await evaluate('document.documentElement.dataset.style'),'clean');
 }finally{await browser.close();fs.rmSync(dir,{recursive:true,force:true});}
});
