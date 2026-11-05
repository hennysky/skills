import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const release=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8'));
export function checkReleaseIdentity(){
 const identity=JSON.parse(fs.readFileSync(path.join(root,'skill-release.json'),'utf8'));
 const skill=fs.readFileSync(path.join(root,'SKILL.md'),'utf8');
 const template=fs.readFileSync(path.join(root,'assets/template.html'),'utf8');
 if(identity.skillId!==release.name||identity.version!==release.version||!skill.includes(`version: "${release.version}"`)||!template.includes(`hennysky-visual-planning ${release.version}`))throw Error('Independent release identity drift');
 return {name:release.name,version:release.version,status:'passed'};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(checkReleaseIdentity()));
