// FEAT-174: ordinary Skill payloads become native local plugin sources.
// This does not install a Skill, alter expert bundles or download content.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,lstat,mkdir,writeFile,rename,rm} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import Ajv from 'ajv/dist/2020.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sha=b=>createHash('sha256').update(b).digest('hex');
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
export function contentDigest(entries){
 const h=createHash('sha256');
 for(const item of [...entries].sort((a,b)=>Buffer.compare(Buffer.from(a.path),Buffer.from(b.path)))){
  const p=Buffer.from(item.path),n=Buffer.alloc(8);n.writeBigUInt64BE(BigInt(p.length));h.update(n).update(p).update(Buffer.from(sha(item.bytes),'hex'));
 }
 return h.digest('hex');
}
export async function packageNativeSkills(output=path.join(root,'dist/native-skill-marketplace'),options={}){
 const sourceFile=options.sourceFile??path.join(root,'plugins/yijie-desktop-skills/bundle-source.json');
 const source=JSON.parse(await readFile(sourceFile,'utf8'));
 assert.equal(source.schema_version,2);assert(Array.isArray(source.skills)&&source.skills.length<=512);assert(source.authorized_distribution_channels.includes('local-development'));
 const ids=new Set();for(const skill of source.skills){assert(!ids.has(skill.id),'duplicate Skill identity');ids.add(skill.id);assert(!skill.asset_kind||skill.asset_kind==='skill','expert resources use their existing producer');}
 const staging=output+'.preparing';await mkdir(staging,{recursive:false});
 try{
  const skills=[],plugins=[];
  for(const skill of source.skills){
   if(skill.release.catalog_status==='blocked'||skill.catalog_entry_mode==='catalog-only')continue;
   assert.equal(skill.catalog_entry_mode,'bundled');assert.equal(skill.release.catalog_status,'installable');assert.equal(skill.license.redistribution_status,'verified');
   const entries=[];
   for(const name of skill.package_files){
    assert(name&&!path.isAbsolute(name)&&path.posix.normalize(name)===name&&!name.startsWith('../')&&!name.includes('\\'));
    const p=path.join(root,skill.source_dir,name),info=await lstat(p);assert(info.isFile()&&!info.isSymbolicLink());
    entries.push({path:name,bytes:await readFile(p)});
   }
   assert(entries.some(e=>e.path==='SKILL.md'),'Skill entrypoint missing');
   const digest=contentDigest(entries),pluginName='yj-builtin-'+sha(Buffer.from(skill.id)).slice(0,24);
   const metadata={name:pluginName,skills:'./skills',mcpServers:{},interface:{displayName:skill.display_name,shortDescription:skill.description,category:skill.category}};
   const revision=sha(Buffer.from(canonical({recipe:1,content:digest,metadata})));
   const version='1.0.0+yj.'+revision.slice(0,32),relative='plugins/'+pluginName;
   await mkdir(path.join(staging,relative,'.codex-plugin'),{recursive:true});
   await writeFile(path.join(staging,relative,'.codex-plugin/plugin.json'),JSON.stringify({...metadata,version},null,2)+'\n');
   for(const e of entries){const p=path.join(staging,relative,'skills/main',e.path);await mkdir(path.dirname(p),{recursive:true});await writeFile(p,e.bytes);}
   skills.push({id:skill.id,content_version:skill.version,content_sha256:digest,source_revision:revision,native_package_version:version,plugin_name:pluginName,display_name:skill.display_name,description:skill.description,category:skill.category,order:skill.order,icon_key:skill.icon.key,required_tools:skill.capabilities.required_tools,source_path:relative,files:entries.map(e=>({path:e.path,sha256:sha(e.bytes),bytes:e.bytes.length}))});
   plugins.push({name:pluginName,source:'./'+relative,policy:{installation:'AVAILABLE',authentication:'ON_INSTALL'},category:skill.category});
  }
  const manifest={schema_version:2,marketplace_name:'yijie-builtin',skills};
  const schema=JSON.parse(await readFile(path.join(root,'contracts/skill-market-v2.schema.json'),'utf8'));
  const ajv=new Ajv({strict:false});ajv.addSchema(schema);const validate=ajv.getSchema(schema.$id+'#/$defs/Bundle');assert(validate(manifest),JSON.stringify(validate.errors));
  await mkdir(path.join(staging,'.agents/plugins'),{recursive:true});
  await writeFile(path.join(staging,'.agents/plugins/marketplace.json'),JSON.stringify({name:'yijie-builtin',interface:{displayName:'易界内置技能'},plugins},null,2)+'\n');
  await writeFile(path.join(staging,'presentation.json'),JSON.stringify(manifest,null,2)+'\n');
  await rename(staging,output);return manifest;
 }catch(e){await rm(staging,{recursive:true,force:true});throw e;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 assert(process.argv.length<=4,'usage: package-native-skill-marketplace.mjs [output] [source-file]');
 const output=process.argv[2]?path.resolve(process.argv[2]):undefined;
 await mkdir(path.dirname(output??path.join(root,'dist/native-skill-marketplace')),{recursive:true});
 const result=await packageNativeSkills(output,{sourceFile:process.argv[3]?path.resolve(process.argv[3]):undefined});console.log('Packaged '+result.skills.length+' native local Skill sources; installed=0.');
}
