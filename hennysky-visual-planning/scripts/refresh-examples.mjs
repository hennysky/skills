import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const entries={
 'class-payment-processors-rendered.html':'payment-processors.class.json',
 'class-payments-rendered.html':'payments.class.json',
 'dataflow-product-analytics.html':'product-analytics.dataflow.json',
 'erd-orders-rendered.html':'orders.erd.json',
 'lifecycle-agent-run.html':'agent-run.lifecycle.json',
 'sequence-cache-miss-request.html':'cache-miss-request.sequence.json',
 'subscription-billing-rendered.html':'subscription-billing.erd.json',
 'timeline-visualplan-dev-activity-rendered.html':'visualplan-dev-activity.timeline.json',
 'timeline-payment-incident-rendered.html':'payment-incident.timeline.json',
 'tree-visualplan-repository-rendered.html':'visualplan-repository.tree.json',
 'tree-payment-platform-rendered.html':'payment-platform.tree.json',
 'waterfall-checkout-request-rendered.html':'checkout-request.waterfall.json',
 'waterfall-example-rebuild-rendered.html':'example-rebuild.waterfall.json',
 'web-app-rendered.html':'web-app.architecture.json',
 'workflow-agent-tool-call-rendered.html':'agent-tool-call.workflow.json'
};
for(const [html,json]of Object.entries(entries)) {
 const type=json.split('.').at(-2);
 const r=spawnSync(process.execPath,[path.join(root,'bin/visualplan.mjs'),'render',type,path.join(root,'examples',json),path.join(root,'examples',html),'--quality','showcase'],{encoding:'utf8',cwd:root});
 if(r.status!==0)throw Error(json+'\n'+r.stdout+r.stderr);
}
console.log('Rebuilt '+Object.keys(entries).length+' native example pages');
