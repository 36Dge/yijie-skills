import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const root=path.resolve('plugins/yijie-desktop-skills/experts/linkfox-expert-aigc-videogen-sale/skills/sales-video');
const sample=JSON.parse(readFileSync(path.join(root,'examples/plan.json')));
const clone=()=>structuredClone(sample);
const hash=b=>createHash('sha256').update(b).digest('hex');
function run(action,value,accepted=true){
 const cwd=mkdtempSync(path.join(tmpdir(),'yijie-sale-normal-'));
 try{
  const bytes=JSON.stringify(value,null,2)+'\n';writeFileSync(path.join(cwd,'source.json'),bytes);
  const args=[path.join(root,'scripts/sales_video.py'),action,'--input','source.json','--output-dir','result'];
  const proc=spawnSync('python3',args,{cwd,encoding:'utf8'});
  if(!accepted){assert.equal(proc.status,2,proc.stderr);assert.equal(existsSync(path.join(cwd,'result')),false);return;}
  assert.equal(proc.status,0,proc.stderr);assert.equal(JSON.parse(proc.stdout).external_calls,0);
  assert.equal(readFileSync(path.join(cwd,'source.json'),'utf8'),bytes);
  assert.equal(readFileSync(path.join(cwd,'result/input.json'),'utf8'),bytes);
  const receipt=JSON.parse(readFileSync(path.join(cwd,'result/receipt.json')));
  assert.equal(receipt.files.length,3);
  for(const f of receipt.files){const b=readFileSync(path.join(cwd,'result',f.path));assert.equal(b.length,f.bytes);assert.equal(hash(b),f.sha256);}
  assert.equal(spawnSync('python3',args,{cwd,encoding:'utf8'}).status,2,'old output preserved');
  assert.equal(readdirSync(path.join(root,'scripts')).some(f=>f==='__pycache__'),false);
  return JSON.parse(readFileSync(path.join(cwd,'result/inspection.json')));
 }finally{rmSync(cwd,{recursive:true,force:true});}
}
const selected=(p=clone(),id=2)=>({plan:p,selection:{plan_sha256:run('prepare',p).plan_sha256,scheme_id:id,user_message:`选择方案${id}，仅准备参数，不提交。`}});
test('sale: real artifacts preserve source and await explicit choice',()=>{
 const r=run('prepare',clone());assert.equal(r.state,'awaiting_user_selection');assert.equal(r.plan.schemes.length,3);assert.equal(r.fact_semantics_verified,false);assert.equal(r.speech_timing_verified,false);
 assert.equal(r.request,undefined);assert.deepEqual(r.plan.brief.unknowns,sample.brief.unknowns);
});
test('sale: exact reviewed spoken claims, duration, voice and model reach request',()=>{
 const r=run('video',selected());assert.equal(r.state,'video_prepared_not_submitted');assert.equal(r.approval_granted,false);
 assert.equal(r.request.toolName,'aigc/multiImageVideoGenAsync');assert.equal(r.request.arguments.voice,true);assert.equal(r.request.arguments.promptOptimizer,false);
 assert.equal(r.request.arguments.videoTime,15);assert.equal(r.request.arguments.isPro,undefined);
 assert.match(r.request.arguments.prompt,/\[0-5s\].*Close-up/);assert.match(r.request.arguments.prompt,/\[10-15s\]/);
 for(const c of sample.brief.claims) assert.ok(r.request.arguments.prompt.includes(c.spoken_text));
 for(const s of ['stainless','12 hours','discount','certified']) assert.equal(r.request.arguments.prompt.includes(s),false);
 assert.equal(r.local_file,null);assert.equal(r.current_tool_schema_verified,false);
 assert.ok(Buffer.byteLength(JSON.stringify(r.request))<16*1024);
});
test('sale: changed brief or plan invalidates prior explicit selection',()=>{
 for(const change of [p=>p.brief.claims[0].spoken_text='A green cup.',p=>p.schemes[0].title='New title',p=>p.brief.video.resolution='480p']){
  const v=selected();change(v.plan);run('video',v,false);
 }
 for(const id of [0,4,true]){const v=selected();v.selection.scheme_id=id;run('video',v,false);}
 const v=selected();v.selection.user_message='';run('video',v,false);
});
test('sale: missing ordinary input and unconfirmed references stop before writing',()=>{
 for(const change of [p=>delete p.brief.language,p=>p.brief.sales_region='',p=>p.schemes.pop(),p=>p.schemes[0].shots[0].claim_ids=['unknown'],p=>p.schemes[0].shots[0].seconds=6,p=>p.schemes[1].shots=structuredClone(p.schemes[0].shots),p=>p.brief.claims.push(p.brief.claims[0])]){const p=clone();change(p);run('prepare',p,false);}
});
test('sale: local plan without public image is usable but cannot make remote request',()=>{
 const p=clone();p.brief.image_urls=[];assert.equal(run('prepare',p).state,'awaiting_user_selection');run('video',selected(p),false);
});
test('sale: model, audio and ratio conflicts never silently change user intent',()=>{
 for(const video of [{voice:false},{videoType:'WAN'},{videoType:'HAPPY_HORSE'},{resolution:'1080p'},{isPro:false},{aspectRatio:'adaptive'},{videoTime:12}]){const p=clone();Object.assign(p.brief.video,video);run('prepare',p,false);}
 const p=clone();Object.assign(p.brief.video,{videoType:'SEED',resolution:'1080p',isPro:true});const r=run('video',selected(p));assert.equal(r.request.arguments.isPro,true);
});
test('sale: long supported facts cannot silently truncate final prompt',()=>{
 const p=clone();p.brief.claims[0].spoken_text='A blue cup. '.repeat(24);for(const s of p.schemes) s.shots=Array.from({length:5},(_,i)=>({seconds:3,framing:s.shots[i%3].framing,claim_ids:['color','capacity']}));run('video',selected(p),false);
});
const requestHash=run('video',selected()).request_sha256;
const observation=(body,stage='create',creation)=>({stage,request_sha256:requestHash,source_operation_id:`native-${stage}`,mcp_result:{structuredContent:body},...(creation?{creation}:{})});
const created=()=>run('observe',observation({taskId:'ordinary-sale-task'}));
test('sale: original task query produces no new request and never implies video completion',()=>{
 const c=created();assert.equal(c.state,'created');assert.deepEqual(c.query_request,{toolName:'aigc/taskQuery',arguments:{taskId:'ordinary-sale-task'}});
 const r=run('observe',observation({taskId:'ordinary-sale-task',status:'PROCESSING'},'query',c));assert.equal(r.state,'processing');assert.equal(r.retry_creation,false);assert.equal(r.result_url,undefined);
});
test('sale: successful video is a URL only, observation keeps original operation identity',()=>{
 const r=run('observe',observation({taskId:'ordinary-sale-task',status:'SUCCESS',resultList:[{type:'video',url:'https://media.example.com/result.mp4'}]},'query',created()));
 assert.equal(r.state,'video_link_ready');assert.equal(r.local_file,null);assert.equal(r.visual_audio_quality,'not_verified');assert.equal(r.creation_operation_id,'native-create');
});
test('sale: ordinary business rejection, task mismatch and missing result remain honest',()=>{
 const c=created();
 for(const [body,state] of [[{taskId:'ordinary-sale-task',status:'FAILED',errorMsg:'额度不足'},'failed'],[{taskId:'another-task',status:'SUCCESS',resultList:[]},'unknown'],[{taskId:'ordinary-sale-task',status:'SUCCESS',resultList:[]},'unknown'],[{code:402},'unknown']]){const r=run('observe',observation(body,'query',c));assert.equal(r.state,state);assert.equal(r.retry_creation,false);}
 const input=observation({taskId:'ordinary-sale-task'},'query',c);input.request_sha256='a'.repeat(64);run('observe',input,false);
});
test('sale: normal MCP envelope and conflicting sources cannot fake readiness',()=>{
 const body={code:200,data:{taskId:'ordinary-sale-task'}};const input=observation(body);input.mcp_result={content:[{type:'text',text:JSON.stringify(body)}]};assert.equal(run('observe',input).state,'created');
 input.mcp_result.structuredContent={taskId:'different'};assert.equal(run('observe',input).state,'unknown');input.mcp_result={isError:true};assert.equal(run('observe',input).reason,'mcp_error');
});
test('sale: connector fixture is the exact generated selection-two request',()=>{
 const expected=JSON.parse(readFileSync('../yijie-connectors/worker/fixtures/linkfox-sale-request.json'));
 assert.deepEqual(run('video',selected()).request,expected);
 run('observe',{...observation({},'query'),creation:[]},false);
});
