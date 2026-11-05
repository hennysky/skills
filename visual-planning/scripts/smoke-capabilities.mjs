import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.resolve(process.env.VISUAL_PLAN_SMOKE_OUT || fs.mkdtempSync(path.join(os.tmpdir(),'visual-all-types-')));
fs.mkdirSync(output,{recursive:true});
const examples={architecture:'web-app.architecture.json',workflow:'agent-tool-call.workflow.json',sequence:'cache-miss-request.sequence.json',dataflow:'product-analytics.dataflow.json',lifecycle:'agent-run.lifecycle.json',erd:'orders.erd.json',class:'payments.class.json',tree:'payment-platform.tree.json',timeline:'payment-incident.timeline.json',waterfall:'checkout-request.waterfall.json'};
const results=[];
for(const [type,example] of Object.entries(examples)) {
 const html=path.join(output,type+'.html');
 const r=spawnSync(process.execPath,[path.join(root,'bin/visualplan.mjs'),'finalize',type,path.join(root,'examples',example),html,'--quality','showcase','--json'],{encoding:'utf8',maxBuffer:10*1024*1024,cwd:output});
 fs.writeFileSync(path.join(output,type+'-stdout.txt'),r.stdout+'\n'+r.stderr);
 let receipt;try{receipt=JSON.parse(r.stdout);}catch{}
 results.push({type,exit:r.status,receipt:receipt?.status||null,html});
 console.log(type+': '+(r.status===0?'passed':'FAILED'));
}
fs.writeFileSync(path.join(output,'smoke-results.json'),JSON.stringify({output,results},null,2)+'\n');
console.log('Evidence: '+output);
if(results.some(r=>r.exit!==0))process.exitCode=1;
