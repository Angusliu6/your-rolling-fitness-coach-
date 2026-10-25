// Node 20+ built-ins only. Smoke test: offline UI state, per-set logging and export.
import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";

const source=readFileSync(new URL("../docs/training-ui.js",import.meta.url),"utf8");

function harness(){
  const ids=[
    "session-date","duration","bodyweight","weight-unit","weight-context","readiness","template",
    "tracker","exercise-list","count","progress-bar","session-notes","feedback",
    "start","back","add","core","new-name","new-sets","copy","download","export-cli",
    "import","reset","before-title"
  ];
  function el(){
    const events={};
    return {value:"",checked:false,textContent:"",innerHTML:"",hidden:false,
      style:{},dataset:{},events,
      addEventListener(n,fn){events[n]=fn;},
      fire(n,ev={}){if(!events[n])throw Error("unbound "+n);events[n](ev);},
      scrollIntoView(){},remove(){},click(){},select(){}};
  }
  const dom=new Map(ids.map(id=>[id,el()]));
  const memory=new Map();
  let lastBlob=null,lastCopy="",downloads=0;
  const context={
    console,Date,JSON,Number,Array,String,Math,Promise,Blob,setTimeout(fn){fn();},
    navigator:{clipboard:{writeText(text){lastCopy=text;return Promise.resolve();}}},
    localStorage:{
      getItem(k){return memory.get(k)||null;},
      setItem(k,v){memory.set(k,v);},
      removeItem(k){memory.delete(k);}
    },
    window:{confirm(){return true;}},
    URL:{createObjectURL(blob){lastBlob=blob;return "blob:example";},revokeObjectURL(){}},
    document:{getElementById(id){if(!dom.has(id))throw Error("missing "+id);return dom.get(id);},
      createElement(){return {...el(),click(){downloads++;}};},
      body:{appendChild(){}}}
  };
  vm.runInNewContext(source,context,{filename:"training-ui.js"});
  function state(){return JSON.parse(memory.get("rolling_fitness_tracker_v2"));}
  function start(weight="",weightContext="unknown"){
    dom.get("bodyweight").value=weight;
    dom.get("weight-context").value=weightContext;
    dom.get("start").fire("click");
  }
  function set(e,s,field,value){
    const target={dataset:{e:String(e),s:String(s),field},value,checked:value===true};
    dom.get("exercise-list").fire("input",{target});
    if(field==="completed"||field==="rir")dom.get("exercise-list").fire("change",{target});
  }
  return {dom,state,start,set,memory,lastBlob:()=>lastBlob,lastCopy:()=>lastCopy,downloads:()=>downloads};
}

test("preflight bodyweight/context, core in 60min plan; no preset completed sets",()=>{
  const app=harness();
  app.start("68.15","after_meal_before_workout");
  const s=app.state();
  assert.equal(s.bodyweight,"68.15");
  assert.equal(s.weight_context,"after_meal_before_workout");
  assert.equal(s.exercises.length,6);
  assert.ok(s.exercises.some(e=>e.muscles.includes("腹部")));
  assert.equal(s.exercises.reduce((t,e)=>t+e.rows.filter(r=>r.completed).length,0),0);
  assert.equal(app.dom.get("tracker").hidden,false);
});

test("each set independently persists load, reps, RIR and completion; no fabrications",()=>{
  const app=harness();app.start();
  app.set(1,0,"load","6");app.set(1,0,"reps","10");app.set(1,0,"rir","2");
  app.set(1,0,"completed",true);
  app.set(1,1,"load","5");
  const s=app.state();
  assert.equal(s.exercises[1].rows[0].load,"6");
  assert.equal(s.exercises[1].rows[0].reps,"10");
  assert.equal(s.exercises[1].rows[0].rir,"2");
  assert.equal(s.exercises[1].rows[0].completed,true);
  assert.equal(s.exercises[1].rows[1].load,"5");
  assert.equal(s.exercises[1].rows[1].completed,false);
  assert.equal(s.exercises[1].rows[2].reps,"");
  assert.match(app.dom.get("count").textContent,/1 \/ 15组/);
});

test("CLI export includes only completed sets, preserves missing numeric fields as null",async()=>{
  const app=harness();app.start("65.2","morning_fasted");
  app.set(1,0,"load","6");app.set(1,0,"completed",true);
  app.set(1,1,"load","5"); // unconfirmed: must not export
  app.dom.get("export-cli").fire("click");
  assert.equal(app.downloads(),1);
  const data=JSON.parse(await app.lastBlob().text());
  assert.equal(data.exercises.length,1);
  assert.equal(data.exercises[0].sets.length,1);
  assert.equal(data.exercises[0].sets[0].kg,6);
  assert.equal(data.exercises[0].sets[0].reps,null);
  assert.equal(data.exercises[0].sets[0].rir,null);
  assert.equal(data.exercises[0].sets[0].type,"work");
});

test("backup retains preflight weight and unconfirmed entries separately",async()=>{
  const app=harness();app.start("66.3","after_meal_before_workout");
  app.set(0,0,"load","20");
  app.dom.get("download").fire("click");
  const backup=JSON.parse(await app.lastBlob().text());
  assert.equal(backup.format,"rolling-fitness-coach-ui");
  assert.equal(backup.session.bodyweight,"66.3");
  assert.equal(backup.session.exercises[0].rows[0].completed,false);
  assert.equal(backup.session.exercises[0].rows[0].load,"20");
});

test("user can swap equipment/name and add abs module without hiding completed data",()=>{
  const app=harness();app.start();
  app.set(0,0,"completed",true);
  app.dom.get("exercise-list").fire("change",
    {target:{dataset:{e:"1",exercise:"name"},value:"器械侧平举"}});
  app.dom.get("core").fire("click");
  assert.equal(app.state().exercises[1].name,"器械侧平举");
  assert.equal(app.state().exercises.length,7);
  assert.equal(app.state().exercises[0].rows[0].completed,true);
});

test("copy summary respects bodyweight context, unknowns and unconfirmed sets",async()=>{
  const app=harness();app.start("67","after_meal_before_workout");
  app.set(0,0,"load","30");app.set(0,0,"reps","12");app.set(0,0,"completed",true);
  app.dom.get("copy").fire("click");
  await Promise.resolve();
  assert.match(app.lastCopy(),/67\.00kg（饭后、训练前）/);
  assert.match(app.lastCopy(),/30kg.*12次/);
  assert.match(app.lastCopy(),/未确认/);
});


test("Chinese jin measurement is normalized for coach summary without losing raw unit",async()=>{
  const app=harness();
  app.dom.get("weight-unit").value="jin";
  app.start("130","after_meal_before_workout");
  assert.equal(app.state().weight_unit,"jin");
  app.dom.get("copy").fire("click");
  await Promise.resolve();
  assert.match(app.lastCopy(),/65.00kg（原始130斤；饭后、训练前）/);
});
