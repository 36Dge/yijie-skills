// Generated from FEAT-158 experts source and referenced authorities; DO NOT EDIT.
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
function canonicalExpertSnapshotText(snapshot,policy){
  const fields=[policy.domain,snapshot.turnOperationId,String(snapshot.bindingRevision),snapshot.expert===null?'none':'expert'];
  if(snapshot.expert!==null)for(const key of ['expertId','version','archiveSha256','roleSha256','knowledgeManifestSha256'])fields.push(snapshot.expert[key]);
  return fields.join('\n')+'\n';
}
function canonicalKnowledgeManifestBytes(resources,policy){
  const ordered=[...resources].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  assert.equal(new Set(ordered.map(r=>r.id)).size,ordered.length);
  const chunks=[Buffer.from(policy.domain+'\n'+ordered.length+'\n','utf8')];
  for(const resource of ordered){
    for(const key of policy.fields){const value=key==='bytes'?String(resource[key]):resource[key];assert.equal(typeof value,'string');const bytes=Buffer.from(value,'utf8');chunks.push(Buffer.from(bytes.length+':','ascii'),bytes);}
    chunks.push(Buffer.from('\n','ascii'));
  }
  return Buffer.concat(chunks);
}
export const snapshotPolicy={"version":1,"algorithm":"sha256","domain":"yijie.expert-snapshot/v1","encoding":"ASCII with actual LF; lower-case hex","lines":["domain","canonical actual turnOperationId","decimal bindingRevision","none OR expert","when expert: expertId","when expert: version","when expert: archiveSha256","when expert: roleSha256","when expert: knowledgeManifestSha256"],"trailingLf":true};
export const knowledgePolicy={"version":1,"algorithm":"sha256","domain":"yijie.expert-knowledge/v1","encoding":"UTF-8: domain + LF + decimal resource count + LF; sort resources by ASCII id; for each field append decimal UTF-8 byte length + ASCII colon + exact UTF-8 bytes; append LF after each resource","fields":["id","title","path","sha256","bytes","content_version","content_status"],"sort":"id ASCII ascending","uniqueKey":"id","bytesField":"bytes is canonical unsigned decimal text","trailingLf":true};
export function expertSnapshotDigest(value){return createHash("sha256").update(canonicalExpertSnapshotText(value,snapshotPolicy)).digest("hex");}
export function knowledgeManifestDigest(resources){return createHash("sha256").update(canonicalKnowledgeManifestBytes(resources,knowledgePolicy)).digest("hex");}
