import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const skip=new Set(['node_modules','.git','output','dist']);
function walk(dir) {return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>skip.has(e.name)?[]:e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const files=walk(process.cwd()).filter(p=>/\.m?js$/.test(p));
for(const file of files) {const r=spawnSync(process.execPath,['--check',file],{encoding:'utf8'});if(r.status!==0)throw Error(file+'\n'+r.stderr);}
console.log('Syntax passed: '+files.length+' JavaScript files');
