/* Rolling Fitness Coach – offline-first, no dependencies, no network calls. */
(function () {
  "use strict";
  var STORAGE_KEY = "rolling_fitness_tracker_v2";
  var dateToday = function () {
    var d = new Date();
    return [d.getFullYear(), String(d.getMonth()+1).padStart(2,"0"), String(d.getDate()).padStart(2,"0")].join("-");
  };
  var DEFAULTS = {
    full: [
      ["上斜推胸",3,"8–12","machine_stack","胸"],
      ["哑铃侧平举",3,"12–20","per_dumbbell","肩"],
      ["高位下拉",3,"8–12","machine_stack","背"],
      ["腿举",2,"10–12","machine_stack","腿"],
      ["坐姿腿弯举",2,"10–15","machine_stack","腿后侧"],
      ["反向卷腹",2,"10–15","bodyweight","腹部"]
    ],
    short: [
      ["上斜推胸",3,"8–12","machine_stack","胸"],
      ["哑铃侧平举",2,"12–20","per_dumbbell","肩"],
      ["高位下拉",2,"8–12","machine_stack","背"],
      ["腿举",2,"10–12","machine_stack","腿"],
      ["反向卷腹",2,"10–15","bodyweight","腹部"]
    ],
    blank: []
  };
  var selectors = {
    date: document.getElementById("session-date"),
    duration: document.getElementById("duration"),
    weight: document.getElementById("bodyweight"),
    context: document.getElementById("weight-context"),
    readiness: document.getElementById("readiness"),
    template: document.getElementById("template"),
    tracker: document.getElementById("tracker"),
    list: document.getElementById("exercise-list"),
    count: document.getElementById("count"),
    progress: document.getElementById("progress-bar"),
    notes: document.getElementById("session-notes"),
    feedback: document.getElementById("feedback")
  };
  function freshSet() { return { load:"", reps:"", rir:"", completed:false }; }
  function makeExercise(item) {
    return {name:item[0], rows:Array.from({length:item[1]},freshSet),
      target:item[2], load_basis:item[3], muscles:[item[4]], equipment:item[0], unit:"kg"};
  }
  function makeState() {
    return {version:2,date:dateToday(),duration:"60",bodyweight:"",weight_context:"unknown",
      readiness:"normal",selected_template:"full",active_template:null,stage:"setup",
      exercises:[],notes:""};
  }
  function safeText(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g,function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  function byId(id){ return document.getElementById(id); }
  function readSaved() {
    try {
      var raw=localStorage.getItem(STORAGE_KEY);
      if (!raw) return makeState();
      var data=JSON.parse(raw);
      if(!validState(data)) return makeState();
      return data;
    } catch(e){return makeState();}
  }
  function validState(d) {
    return d && d.version===2 && typeof d.date==="string" && Array.isArray(d.exercises)
      && d.exercises.length<=60 && d.exercises.every(function(e){
        return e && typeof e.name==="string" && e.name.length<=100
          && Array.isArray(e.rows) && e.rows.length<=30 && e.rows.every(function(r){
            return r && typeof r==="object" && typeof r.completed==="boolean";
          });
      });
  }
  var state=readSaved();
  function persist() {
    try { localStorage.setItem(STORAGE_KEY,JSON.stringify(state)); }
    catch(e) { setFeedback("当前浏览器阻止本地保存。请使用 JSON 导出备份。"); }
  }
  function setFeedback(t) { selectors.feedback.textContent=t || ""; }
  function numberOrNull(v) {
    if(v==="" || v===undefined || v===null) return null;
    var n=Number(v);
    return Number.isFinite(n) && n>=0 ? n:null;
  }
  function integerOrNull(v) {
    var n=numberOrNull(v);
    return n!==null && Number.isInteger(n) ? n:null;
  }
  function labelBasis(b) {
    return ({machine_stack:"器械配重",per_dumbbell:"每只哑铃",barbell_total:"杠铃总重",
      bodyweight:"自重/外加负重",other:"其他口径"})[b] || "未注明";
  }
  function readSetup() {
    state.date=selectors.date.value || dateToday();
    state.duration=selectors.duration.value || "60";
    state.bodyweight=selectors.weight.value;
    state.weight_context=selectors.context.value;
    state.readiness=selectors.readiness.value;
    state.selected_template=selectors.template.value;
    persist();
  }
  function loadSetup() {
    selectors.date.value=state.date;
    selectors.duration.value=state.duration;
    selectors.weight.value=state.bodyweight;
    selectors.context.value=state.weight_context;
    selectors.readiness.value=state.readiness;
    selectors.template.value=state.selected_template;
    selectors.notes.value=state.notes;
  }
  function showStage() {
    selectors.tracker.hidden=state.stage!=="workout";
    if(state.stage==="workout") render();
  }
  function rowsCount() {
    var c=0,t=0;
    state.exercises.forEach(function(e){e.rows.forEach(function(r){t++;if(r.completed)c++;});});
    return {complete:c,total:t};
  }
  function updateProgress() {
    var c=rowsCount();
    selectors.count.textContent=c.complete+" / "+c.total+"组";
    selectors.progress.style.width=(c.total ? Math.round(c.complete/c.total*100):0)+"%";
  }
  function setBlock(r,ei,si) {
    var basis=state.exercises[ei].load_basis;
    var options='<option value="">未记录</option>';
    [0,1,2,3,4,5].forEach(function(n){
      options+='<option value="'+n+'"'+(String(r.rir)===String(n)?' selected':'')+'>'+n+'</option>';
    });
    return '<div class="set-row">'+
      '<div class="set-top"><strong>第 '+(si+1)+' 组</strong><label class="check">'+
      '<input type="checkbox" data-e="'+ei+'" data-s="'+si+'" data-field="completed"'+
      (r.completed?' checked':'')+'> 已完成</label></div>'+
      '<div class="set-fields">'+
      '<label>重量 kg<small>'+safeText(labelBasis(basis))+'</small><input type="number" inputmode="decimal" min="0" max="2000" step="any" placeholder="可空" data-e="'+ei+'" data-s="'+si+'" data-field="load" value="'+safeText(r.load)+'"></label>'+
      '<label>次数<input type="number" inputmode="numeric" min="0" max="999" step="1" placeholder="可空" data-e="'+ei+'" data-s="'+si+'" data-field="reps" value="'+safeText(r.reps)+'"></label>'+
      '<label>RIR<select data-e="'+ei+'" data-s="'+si+'" data-field="rir">'+options+'</select></label>'+
      '</div></div>';
  }
  function render(){
    selectors.list.innerHTML=state.exercises.map(function(e,i){
      var bases=["machine_stack","per_dumbbell","barbell_total","bodyweight","other"];
      return '<article class="exercise"><div class="exercise-title">'+
        '<div class="exercise-heading"><span class="exercise-index">'+(i+1)+'</span>'+
        '<div><h3>'+safeText(e.name)+'</h3><span class="muted">目标 '+safeText(e.target||"自主设定")+
        ' 次 · '+e.rows.filter(function(r){return r.completed;}).length+'/'+e.rows.length+'组完成</span></div></div>'+
        '<button data-action="remove-exercise" data-e="'+i+'" class="small-danger">删除动作</button></div>'+
        '<div class="exercise-settings"><label>替换 / 修改动作名<input data-e="'+i+'" data-exercise="name" maxlength="100" value="'+safeText(e.name)+'"></label>'+
        '<label>负重口径<select data-e="'+i+'" data-exercise="load_basis">'+
        bases.map(function(b){return '<option value="'+b+'"'+(e.load_basis===b?' selected':'')+'>'+labelBasis(b)+'</option>';}).join('')+
        '</select></label></div>'+
        e.rows.map(function(r,j){return setBlock(r,i,j);}).join('')+
        '<div class="controls"><button data-action="add-set" data-e="'+i+'" type="button">＋ 加一组</button>'+
        '<button data-action="remove-set" data-e="'+i+'" type="button">－ 删除末组</button></div>'+
        '</article>';
    }).join('') || '<p class="hint">还没有动作。请在下方添加你的第一个动作。</p>';
    updateProgress();
  }
  function completeData(){
    var exercises=state.exercises.map(function(e){
      var rows=e.rows.map(function(r){return r.completed?r:null;}).filter(Boolean);
      return {exercise:e,rows:rows};
    }).filter(function(x){return x.rows.length;});
    return exercises;
  }
  function makeSummary(){
    var contexts={unknown:"测量条件未知",morning_fasted:"晨起空腹",before_workout:"训练前",
      after_meal_before_workout:"饭后、训练前",after_workout:"训练后"};
    var lines=["Rolling Fitness Coach 训练反馈", "日期："+state.date,
      "计划时长："+state.duration+"分钟",
      "体重："+(state.bodyweight?state.bodyweight+"kg（"+contexts[state.weight_context]+"）":"未记录"),
      "今日恢复："+state.readiness,"已完成组数："+rowsCount().complete+"/"+rowsCount().total];
    state.exercises.forEach(function(e){
      lines.push(e.name+"（"+labelBasis(e.load_basis)+"）：");
      e.rows.forEach(function(r,j){
        lines.push("  第"+(j+1)+"组 "+
          (r.load===""?"重量未知":r.load+"kg")+" × "+(r.reps===""?"次数未知":r.reps+"次")+
          "，RIR "+(r.rir===""?"未知":r.rir)+"，"+(r.completed?"已完成":"未确认"));
      });
    });
    lines.push("感受："+(state.notes||"未填写"));
    lines.push("请只统计确认完成的训练组，缺失字段保持未知，并按疲劳、疼痛和目标动态调整。");
    return lines.join("\n");
  }
  function bundle() {
    return {format:"rolling-fitness-coach-ui",version:2,
      exported_at:new Date().toISOString(),session:state};
  }
  function cliWorkout(){
    var e=completeData().map(function(x){
      return {name:x.exercise.name,muscles:x.exercise.muscles||[],
        notes:"负重口径："+labelBasis(x.exercise.load_basis)+
          "；器械："+x.exercise.equipment,
        sets:x.rows.map(function(r){return {kg:numberOrNull(r.load),
          reps:integerOrNull(r.reps),rir:numberOrNull(r.rir),type:"work"};})};
    });
    return {date:state.date,duration_min:numberOrNull(state.duration),fatigue_0_10:null,
      pain_notes:state.readiness==="pain"?"用户报告疼痛；未做医学诊断。":"",
      notes:state.notes,exercises:e};
  }
  function saveFile(data,name){
    var blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json;charset=utf-8"});
    var url=URL.createObjectURL(blob);var a=document.createElement("a");
    a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(url);},1000);
  }
  function copyText(t){
    if(navigator.clipboard && navigator.clipboard.writeText){
      return navigator.clipboard.writeText(t);
    }
    var tbox=document.createElement("textarea");tbox.value=t;
    tbox.style.position="fixed";tbox.style.left="-9999px";
    document.body.appendChild(tbox);tbox.select();
    var ok=document.execCommand("copy");tbox.remove();
    return ok?Promise.resolve():Promise.reject(new Error("copy unavailable"));
  }
  byId("start").addEventListener("click",function(){
    readSetup();
    if(state.active_template!==state.selected_template) {
      if(state.exercises.some(function(e){return e.rows.some(function(r){return r.completed;});}) &&
         !window.confirm("更换计划模板将清除当前逐组记录。建议先导出备份，确认继续吗？")) return;
      state.exercises=DEFAULTS[state.selected_template].map(makeExercise);
      state.active_template=state.selected_template;
    }
    state.stage="workout";persist();showStage();selectors.tracker.scrollIntoView({behavior:"smooth"});
  });
  byId("back").addEventListener("click",function(){
    state.stage="setup";persist();showStage();document.getElementById("before-title").scrollIntoView({behavior:"smooth"});
  });
  byId("add").addEventListener("click",function(){
    var name=byId("new-name").value.trim();
    var n=Number(byId("new-sets").value);
    if(!name || name.length>100 || !Number.isInteger(n)||n<1||n>12) {
      setFeedback("请填写动作名称及1–12组的计划组数。");return;
    }
    state.exercises.push(makeExercise([name,n,"自主设定","other","其他"]));
    byId("new-name").value="";persist();render();setFeedback("已添加动作："+name);
  });
  byId("core").addEventListener("click",function(){
    state.exercises.push(makeExercise(["反向卷腹",2,"10–15","bodyweight","腹部"]));
    persist();render();setFeedback("已追加腹部训练。若时间不足，可减少其他低优先级组。");
  });
  selectors.list.addEventListener("input",function(ev){
    var el=ev.target;
    var ei=Number(el.dataset.e);
    if(!Number.isInteger(ei)||!state.exercises[ei])return;
    var e=state.exercises[ei];
    if(el.dataset.exercise==="name"){
      e.name=el.value; persist();return;
    }
    if(el.dataset.field){
      var si=Number(el.dataset.s);
      var r=e.rows[si];if(!r)return;
      var field=el.dataset.field;
      if(field!=="completed" && field!=="load" && field!=="reps" && field!=="rir")return;
      if(field==="completed")r.completed=el.checked;
      else r[field]=el.value;
      persist();updateProgress();
    }
  });
  selectors.list.addEventListener("change",function(ev){
    var el=ev.target;
    var ei=Number(el.dataset.e);
    if(!Number.isInteger(ei)||!state.exercises[ei])return;
    var e=state.exercises[ei];
    if(el.dataset.exercise==="load_basis")e.load_basis=el.value;
    if(el.dataset.field==="completed") {
      var r=e.rows[Number(el.dataset.s)];if(r)r.completed=el.checked;
    }
    if(el.dataset.field==="rir") {
      var row=e.rows[Number(el.dataset.s)];if(row)row.rir=el.value;
    }
    if(el.dataset.exercise==="name"){ e.name=el.value.trim()||"未命名动作"; }
    persist();render();
  });
  selectors.list.addEventListener("click",function(ev){
    var el=ev.target.closest("[data-action]");
    if(!el)return;
    var i=Number(el.dataset.e),e=state.exercises[i];if(!e)return;
    var op=el.dataset.action;
    if(op==="add-set"){
      if(e.rows.length>=30){setFeedback("单动作最多记录30组。");return;}
      e.rows.push(freshSet());
    } else if(op==="remove-set"){
      if(!e.rows.length)return;
      if(e.rows[e.rows.length-1].completed &&
        !window.confirm("最后一组已标记完成，确定删除吗？"))return;
      e.rows.pop();
    } else if(op==="remove-exercise"){
      if(e.rows.some(function(r){return r.completed;}) &&
        !window.confirm("这个动作有已完成记录，确定删除吗？"))return;
      state.exercises.splice(i,1);
    }
    persist();render();
  });
  ["date","duration","weight","context","readiness","template"].forEach(function(k){
    selectors[k].addEventListener("change",readSetup);
  });
  selectors.notes.addEventListener("input",function(){
    state.notes=this.value;persist();
  });
  byId("copy").addEventListener("click",function(){
    copyText(makeSummary()).then(function(){setFeedback("训练反馈已复制，可以粘贴到 AI 教练对话。");})
      .catch(function(){setFeedback("自动复制失败，请使用本地 JSON 导出。");});
  });
  byId("download").addEventListener("click",function(){
    saveFile(bundle(),"rolling-fitness-backup-"+state.date+".json");
    setFeedback("已导出本地备份，包含已填写的体重条件和逐组信息。");
  });
  byId("export-cli").addEventListener("click",function(){
    var output=cliWorkout();
    if(!output.exercises.length){setFeedback("尚无已完成训练组，不能导出正式训练日志。");return;}
    saveFile(output,"rolling-fitness-workout-"+state.date+".json");
    setFeedback("已导出与 scripts/coach_log.py add-workout 兼容的已完成训练 JSON；体重请通过 add-weight 另存。");
  });
  byId("import").addEventListener("change",function(ev){
    var f=ev.target.files&&ev.target.files[0];if(!f)return;
    if(f.size>2000000){setFeedback("文件过大，最多2MB。");return;}
    var reader=new FileReader();
    reader.onload=function(){
      try {
        var data=JSON.parse(reader.result);
        if(data.format!=="rolling-fitness-coach-ui" || !validState(data.session)){
          throw new Error("不是本页导出的 v2 备份");
        }
        if(!window.confirm("导入将覆盖本浏览器当前记录，是否继续？"))return;
        state=data.session;persist();loadSetup();showStage();setFeedback("导入成功。");
      }catch(e){setFeedback("导入失败："+e.message);}
    };
    reader.readAsText(f);
    ev.target.value="";
  });
  byId("reset").addEventListener("click",function(){
    if(!window.confirm("删除本页当前浏览器保存的体重及逐组训练记录？建议先导出备份。"))return;
    try {localStorage.removeItem(STORAGE_KEY);}catch(e){}
    state=makeState();loadSetup();showStage();setFeedback("本页本机记录已清除。");
  });
  loadSetup();showStage();
}());
