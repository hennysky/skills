import fs from 'node:fs';
import path from 'node:path';
const upstream=new RegExp(['ar','chi','fy'].join(''),'i');
const retired=[new RegExp(['hai','na'].join(''),'i'),new RegExp(['海','纳'].join('')),new RegExp(['海','納'].join(''))];
const skip=new Set(['node_modules','.git','output','dist']);
function walk(dir) {return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>skip.has(e.name)?[]:e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const violations=[];let count=0;
for(const file of walk(process.cwd())) {
 const rel=path.relative(process.cwd(),file);
 if(retired.some(pattern=>pattern.test(rel)))violations.push(rel+' (retired filename)');
 const bytes=fs.readFileSync(file);if(bytes.includes(0))continue;
 const original=bytes.toString('utf8');
 if(retired.some(pattern=>pattern.test(original)))violations.push(rel+' (retired product identity)');
 if(rel==='LICENSE'||rel.startsWith('licenses'+path.sep)||path.basename(file)==='LICENSE')continue;
 if(upstream.test(rel))violations.push(rel+' (upstream filename)');
 const text=original.split('\n').filter(l=>!/^Copyright \(c\) 2026 tt-a1i \(/.test(l)).join('\n');
 if(upstream.test(text)||/https?:\/\/[^\s]*tt-a1i/i.test(text))violations.push(rel+' (upstream product identity)');
 count++;
}
if(violations.length)throw Error('Obsolete product identity outside preserved legal notices: '+violations.join(', '));
console.log('Neutral product identity passed: '+count+' files; copyright/license provenance preserved');
