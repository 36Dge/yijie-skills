import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {packageNativeSkills} from '../scripts/package-native-skill-marketplace.mjs';

test('native offers package normal removal, addition, blocked entries and an empty release',async()=>{
 const dir=await mkdtemp(path.join(os.tmpdir(),'yijie-native-offers-'));
 try{
  const source=JSON.parse(await readFile(new URL('../plugins/yijie-desktop-skills/bundle-source.json',import.meta.url),'utf8'));
  const extra={...structuredClone(source.skills[0]),id:'yijie.sourcing-selection.ordinary-release-addition',display_name:'普通新增目录项'};
  const variants=[['removed',source.skills.slice(1),37],['added',[...source.skills,extra],39],['blocked',source.skills.map((s,i)=>i? s:{...s,release:{...s.release,catalog_status:'blocked'}}),37],['empty',[],0]];
  for(const [label,skills,count] of variants){
   const input=path.join(dir,label+'.json');await writeFile(input,JSON.stringify({...source,skills}));
   const out=path.join(dir,label),manifest=await packageNativeSkills(out,{sourceFile:input});
   assert.equal(manifest.skills.length,count);
   const native=JSON.parse(await readFile(path.join(out,'.agents/plugins/marketplace.json'),'utf8'));
   assert.equal(native.plugins.length,count);
   assert.equal(new Set(manifest.skills.map(s=>s.id)).size,count);
   if(count) assert.equal(await readFile(path.join(out,manifest.skills[0].source_path,'skills/main/SKILL.md'),'utf8'),await readFile(path.resolve(skills.find(s=>s.id===manifest.skills[0].id).source_dir,'SKILL.md'),'utf8'));
  }
 }finally{await rm(dir,{recursive:true,force:true});}
});
