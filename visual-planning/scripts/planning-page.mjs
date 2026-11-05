#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { release } from './release-identity.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(root, 'bin/visualplan.mjs');
const types = new Set(['architecture','workflow','sequence','dataflow','lifecycle','erd','class','tree','timeline','waterfall']);
const hash = value => createHash('sha256').update(value).digest('hex');
const names = { plan: 'DSH-实施计划.md', diagram: 'diagram.json', candidate: 'candidate.visualplan.md', html: '规划页.html' };

export function compilePlan(markdown, type, locale = 'zh-CN') {
  if (!types.has(type)) throw new Error('Unsupported native diagram type: '+type);
  if (!['zh-CN','zh-TW','en','es','ko','ar'].includes(locale)) throw new Error('Unsupported locale');
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  if (!/^# [^#]/.test(lines[0] || '')) throw new Error('Plan must begin with one # title');
  const intro = [], sections = [];
  let current = intro, fence = null;
  for (let i=1; i<lines.length; i++) {
    const line=lines[i], marker=line.match(/^\s*(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence=marker[1][0];
      else if (marker[1][0]===fence) fence=null;
      current.push(line); continue;
    }
    if (!fence && /^###/.test(line)) throw new Error('Use level-two sections; preserve details in flat tables/lists');
    if (!fence && /^## /.test(line)) {
      const heading=line.slice(3).trim();
      if (/\{#[^}]*\}/.test(heading)) throw new Error('Planning source headings must be plain text; navigation IDs are generated');
      const section={id:'section-'+(sections.length+1), heading, lines:[]};
      sections.push(section); current=section.lines;
    } else current.push(line);
  }
  if (fence) throw new Error('Unclosed code fence');
  if (!sections.length) throw new Error('Plan needs at least one complete implementation section');
  if (!/^- \[[ xX]\] .+/m.test(markdown)) throw new Error('Plan needs concrete checklist tasks');
  const english=locale==='en';
  const back=`[${english?'Contents':'返回目录'}](block:planning-nav) · [${english?'Planning diagram':'返回规划图'}](block:planning-map)`;
  const nav=sections.map(s=>`- [${s.heading}](block:${s.id})`).join('\n');
  const title=lines[0].replace(/\s*\{#[^}]*\}\s*$/, '');
  const candidate=[title+' {#planning-page}',intro.join('\n').trim(),`@meta locale=${locale} style=clean layout=planning`,
    `## ${english?'Contents':'章节目录'} {#planning-nav span=12}`,`- [${english?'Planning diagram':'规划图'}](block:planning-map)\n`+nav,
    `## ${english?'Planning diagram':'规划图'} {#planning-map span=12}`,`@diagram ${type} id=planning-flow source=diagram.json`,back,
    ...sections.flatMap(s=>[`## ${s.heading} {#${s.id} span=12}`,s.lines.join('\n').trim(),back])].join('\n\n')+'\n';
  return {candidate, sections:sections.map(({id,heading})=>({id,heading}))};
}

function execute(args, cwd) {
  const result=spawnSync(process.execPath,[cli,...args],{cwd,encoding:'utf8',maxBuffer:12*1024*1024});
  if (result.status!==0) throw new Error(`Generation/check failed (${result.status}):\n${result.stdout}\n${result.stderr}`);
  return result.stdout;
}

export function build({plan,diagram,type='workflow',out,locale='zh-CN',repoRoot}) {
  const output=path.resolve(out), planBytes=fs.readFileSync(plan), diagramBytes=fs.readFileSync(diagram);
  const spec=JSON.parse(diagramBytes);
  if (spec.diagram_type!==type) throw new Error('Diagram type differs from --type');
  const {candidate,sections}=compilePlan(planBytes.toString('utf8'),type,locale);
  if (fs.existsSync(output) && fs.readdirSync(output).length) throw new Error('Output directory is not empty; choose a new revision directory');
  fs.mkdirSync(output,{recursive:true});
  fs.writeFileSync(path.join(output,names.plan),planBytes);
  fs.writeFileSync(path.join(output,names.diagram),diagramBytes);
  fs.writeFileSync(path.join(output,names.candidate),candidate);
  const result=execute(['finalize','explainer',names.candidate,names.html,'--json',...(repoRoot?['--repo-root',path.resolve(repoRoot)]:[])],output);
  fs.writeFileSync(path.join(output,'generation-result.json'),result);
  const files=Object.fromEntries(Object.values(names).map(name=>[name,hash(fs.readFileSync(path.join(output,name)))]));
  const manifest={schemaVersion:1,product:'visual-planning',version:release.version,type,locale,sections,files,
    validation:{artifact:'passed',browser:'not-run',visual:'not-run'},checklist:'Local reading progress; not execution acceptance'};
  fs.writeFileSync(path.join(output,'planning-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  return check({out:output});
}

export function check({out}) {
  const output=path.resolve(out), manifest=JSON.parse(fs.readFileSync(path.join(output,'planning-manifest.json'),'utf8'));
  if (manifest.schemaVersion!==1 || manifest.product!=='visual-planning') throw new Error('Unsupported planning manifest');
  const expected=Object.values(names).sort();
  if (JSON.stringify(Object.keys(manifest.files).sort())!==JSON.stringify(expected)) throw new Error('Incomplete planning file manifest');
  for (const name of expected) {
    if (hash(fs.readFileSync(path.join(output,name)))!==manifest.files[name]) throw new Error('Content changed; rebuild the complete plan: '+name);
  }
  const generated=compilePlan(fs.readFileSync(path.join(output,names.plan),'utf8'),manifest.type,manifest.locale);
  if (generated.candidate!==fs.readFileSync(path.join(output,names.candidate),'utf8')) throw new Error('Page source no longer contains the canonical complete plan');
  const spec=JSON.parse(fs.readFileSync(path.join(output,names.diagram),'utf8'));
  if (spec.diagram_type!==manifest.type) throw new Error('Diagram type mismatch');
  execute(['check',names.html,'--require-provenance','--json'],output);
  return {status:'passed',out:output,html:path.join(output,names.html),markdown:path.join(output,names.plan),sections:generated.sections.length,browser:'not-run-by-this-command'};
}

function args(argv) {
  const [command,...tail]=argv, result={};
  for(let i=0;i<tail.length;i+=2) {
    if (!/^--[a-z-]+$/.test(tail[i]) || !tail[i+1] || tail[i+1].startsWith('--')) throw new Error('Expected --option value pairs');
    const key=tail[i].slice(2);
    if (!['plan','diagram','type','out','locale','repo-root'].includes(key) || key in result) throw new Error('Unknown or duplicate option: '+key);
    result[key==='repo-root'?'repoRoot':key]=tail[i+1];
  }
  if (!['build','check'].includes(command) || !result.out || (command==='build' && (!result.plan||!result.diagram))) throw new Error('Use build --plan plan.md --diagram diagram.json --out new-directory [--type workflow], or check --out directory');
  return {command,result};
}

if (process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try {const {command,result}=args(process.argv.slice(2));console.log(JSON.stringify(command==='build'?build(result):check(result),null,2));}
  catch(error) {console.error(error.message);process.exitCode=1;}
}
