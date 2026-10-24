#!/usr/bin/env python3
"""Private local SQLite log & conservative next-session prescription.

No network or ChatGPT persistence is implied. Python 3.9+, standard library only.
"""
import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY, performed_on TEXT NOT NULL, status TEXT NOT NULL
    CHECK(status IN ('completed','partial')),
  fatigue INTEGER CHECK(fatigue IS NULL OR fatigue BETWEEN 0 AND 10),
  pain INTEGER NOT NULL DEFAULT 0 CHECK(pain IN (0,1)),
  notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS actual_sets (
  id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES sessions(id),
  exercise TEXT NOT NULL, equipment TEXT NOT NULL, load_basis TEXT NOT NULL,
  unit TEXT NOT NULL CHECK(unit IN ('kg','lb')),
  set_no INTEGER NOT NULL CHECK(set_no >= 1),
  set_kind TEXT NOT NULL DEFAULT 'work' CHECK(set_kind IN ('work','warmup')),
  load REAL CHECK(load IS NULL OR load >= 0),
  reps INTEGER CHECK(reps IS NULL OR reps >= 0),
  rir REAL CHECK(rir IS NULL OR rir BETWEEN 0 AND 10),
  form TEXT NOT NULL DEFAULT 'unknown' CHECK(form IN ('good','unknown','compromised')),
  failure INTEGER NOT NULL DEFAULT 0 CHECK(failure IN (0,1)),
  rest_seconds INTEGER CHECK(rest_seconds IS NULL OR rest_seconds >= 0),
  eccentric_seconds REAL CHECK(eccentric_seconds IS NULL OR eccentric_seconds >= 0),
  concentric_seconds REAL CHECK(concentric_seconds IS NULL OR concentric_seconds >= 0),
  UNIQUE(session_id, exercise, equipment, load_basis, unit, set_no)
);
CREATE INDEX IF NOT EXISTS ix_sets_lookup ON actual_sets(exercise,equipment,load_basis,unit,session_id);
CREATE TABLE IF NOT EXISTS prescriptions (
  id INTEGER PRIMARY KEY, created_on TEXT NOT NULL,
  exercise TEXT NOT NULL, equipment TEXT NOT NULL, load_basis TEXT NOT NULL,
  unit TEXT NOT NULL, rep_min INTEGER NOT NULL, rep_max INTEGER NOT NULL,
  proposed_load REAL, sets INTEGER NOT NULL, rest_seconds INTEGER NOT NULL,
  eccentric_seconds REAL NOT NULL, concentric_seconds REAL NOT NULL,
  decision TEXT NOT NULL, rationale TEXT NOT NULL, planned_sets_json TEXT NOT NULL
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def must(condition, message):
    if not condition:
        raise ValueError(message)


def parse_session(doc):
    must(isinstance(doc, dict), 'Expected a JSON object')
    date.fromisoformat(doc['date'])
    must(doc.get('status', 'completed') in ('completed','partial'), 'Invalid session status')
    must(isinstance(doc.get('exercises'), list) and doc['exercises'], 'Missing exercises')
    if doc.get('fatigue') is not None:
        must(isinstance(doc['fatigue'],int) and 0 <= doc['fatigue'] <= 10, 'Invalid fatigue')
    must(isinstance(doc.get('pain',False), bool), 'pain must be true or false')
    for exercise in doc['exercises']:
        for key in ('exercise','equipment','load_basis','unit'):
            must(isinstance(exercise.get(key),str) and exercise[key].strip(), f'Missing {key}')
        must(exercise['unit'] in ('kg','lb'), 'Unit must be kg/lb')
        must(isinstance(exercise.get('sets'),list) and exercise['sets'], 'Missing sets')
        for index,s in enumerate(exercise['sets'],1):
            must(isinstance(s,dict), 'Invalid set')
            must(s.get('kind','work') in ('work','warmup'),'Invalid set kind')
            must(s.get('form','unknown') in ('good','unknown','compromised'),'Invalid form')
            must(isinstance(s.get('failure',False), bool),'failure must be boolean')
            for k in ('load','reps','rir','rest_seconds','eccentric_seconds','concentric_seconds'):
                if s.get(k) is not None:
                    must(isinstance(s[k],(int,float)) and not isinstance(s[k],bool) and s[k]>=0,f'Invalid {k}')
            if s.get('reps') is not None:
                must(isinstance(s['reps'],int),'reps must be integer')
            if s.get('rir') is not None:
                must(s['rir']<=10, 'RIR out of bounds')
            if s.get('set_no') is not None:
                must(s['set_no']==index,'Sets must be sequential')
    return doc


def add_session(conn, doc):
    doc=parse_session(doc)
    with conn:
        cur=conn.execute('INSERT INTO sessions(performed_on,status,fatigue,pain,notes) VALUES (?,?,?,?,?)',
                    (doc['date'],doc.get('status','completed'),doc.get('fatigue'),int(doc.get('pain',False)),doc.get('notes','')))
        sid=cur.lastrowid
        for e in doc['exercises']:
            for i,s in enumerate(e['sets'],1):
                conn.execute('''INSERT INTO actual_sets
                (session_id,exercise,equipment,load_basis,unit,set_no,set_kind,load,reps,rir,form,failure,rest_seconds,eccentric_seconds,concentric_seconds)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (sid,e['exercise'],e['equipment'],e['load_basis'],e['unit'],i,s.get('kind','work'),s.get('load'),s.get('reps'),s.get('rir'),s.get('form','unknown'),int(s.get('failure',False)),s.get('rest_seconds'),s.get('eccentric_seconds'),s.get('concentric_seconds')))
    return sid


def history(conn,exercise,equipment,load_basis,unit):
    return conn.execute('''SELECT a.*,s.performed_on,s.fatigue,s.pain,s.status FROM actual_sets a JOIN sessions s ON s.id=a.session_id
    WHERE a.exercise=? AND a.equipment=? AND a.load_basis=? AND a.unit=? AND a.set_kind='work'
    ORDER BY s.performed_on DESC,s.id DESC,a.set_no''',(exercise,equipment,load_basis,unit)).fetchall()


def next_load(value,increment,direction):
    # fixed machine/dumbbell increments, not arbitrary unachievable weights
    ticks=round(value/increment)
    if direction>0:
        ticks=int(value/increment)+1
    elif direction<0:
        ticks=max(0,int(value/increment)-1)
    return round(ticks*increment,4)


def prescribe(conn,exercise,equipment,load_basis,unit,rep_min=8,rep_max=12,sets=3,increment=2.5,
              readiness='normal',rest_seconds=120,eccentric_seconds=2.0,concentric_seconds=1.0,save=False):
    must(unit in ('kg','lb') and all(isinstance(x,str) and x.strip() for x in (exercise,equipment,load_basis)),'Specify comparable exercise/equipment/load basis/unit')
    must(isinstance(rep_min,int) and isinstance(rep_max,int) and 1<=rep_min<=rep_max<=30,'Invalid rep range')
    must(isinstance(sets,int) and 1<=sets<=12,'Invalid number of sets')
    must(increment>0 and rest_seconds>=30,'Invalid increment/rest')
    must(readiness in ('normal','low','good','pain'),'Invalid readiness')
    must(eccentric_seconds>0 and concentric_seconds>0,'Tempo must be positive')
    h=history(conn,exercise,equipment,load_basis,unit)
    latest=[]
    if h:
        sid=h[0]['session_id'];latest=[dict(r) for r in h if r['session_id']==sid]
    msg='';decision='baseline';load=None;adjusted_sets=sets
    if readiness=='pain':
        decision='stop';adjusted_sets=0;msg='Pain reported: do not prescribe loaded exercise. Assess before returning.'
    elif not latest:
        decision='baseline';msg='No comparable completed work sets. Choose a comfortable trial load and log per-set reps, RIR, form and equipment.'
    else:
        loads={r['load'] for r in latest};last=latest[0]
        full=all(r['load'] is not None and r['reps'] is not None and r['rir'] is not None and r['form']=='good' and not r['pain'] and r['status']=='completed' for r in latest)
        if not full or len(loads)!=1:
            decision='verify';msg='Prior data are incomplete, unverified, painful, partial or mixed-load. No automatic weight increase; confirm a clean comparable working session.'
            load=next(iter(loads)) if len(loads)==1 else None
        else:
            load=last['load']
            if readiness=='low':
                decision='recover';adjusted_sets=max(1,sets-1)
                msg='Lower readiness: reduce one set, keep the last load only if it moves comfortably; prioritize recovery.'
            elif any(r['form']=='compromised' or r['failure'] and r['reps']<rep_min for r in latest):
                decision='reduce';load=next_load(load,increment,-1)
                msg='Early failure or form breakdown: reduce one available load step; rebuild clean reps, avoid testing max.'
            elif all(r['reps']>=rep_max and r['rir']>=1 and not r['failure'] for r in latest):
                decision='increase';load=next_load(load,increment,1)
                msg='All logged working sets reached the upper rep limit with good form and at least one rep in reserve: add the smallest available load step.'
            else:
                decision='repeat';msg='Keep load and build clean repetitions within the rep range before adding weight.'
    targets=[]
    for i in range(adjusted_sets):
        if decision=='repeat' and i<len(latest) and latest[i]['reps'] is not None:
            target=min(rep_max,max(rep_min,latest[i]['reps']+1))
        elif decision in ('increase','reduce'):
            target=rep_min
        else:
            target=rep_min
        targets.append({'set':i+1,'load':load,'reps_target':target,'reps_range':[rep_min,rep_max],
                        'target_rir':[1,3],'rest_seconds':rest_seconds,
                        'eccentric_seconds':eccentric_seconds,'concentric_seconds':concentric_seconds})
    result={'exercise':exercise,'equipment':equipment,'load_basis':load_basis,'unit':unit,
            'decision':decision,'rationale':msg,'source_session_id':latest[0]['session_id'] if latest else None,
            'last_sets':[{'load':r['load'],'reps':r['reps'],'rir':r['rir'],'failure':bool(r['failure'])} for r in latest],
            'sets':targets,'disclaimer':'Prescription is a suggestion, not a completed workout. Use only comparable equipment; adapt to pain, recovery and technique.'}
    if save:
        with conn:
            conn.execute('''INSERT INTO prescriptions(created_on,exercise,equipment,load_basis,unit,rep_min,rep_max,proposed_load,sets,rest_seconds,eccentric_seconds,concentric_seconds,decision,rationale,planned_sets_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (date.today().isoformat(),exercise,equipment,load_basis,unit,rep_min,rep_max,load,adjusted_sets,rest_seconds,eccentric_seconds,concentric_seconds,decision,msg,json.dumps(targets,ensure_ascii=False)))
    return result


def personal_records(conn,exercise,equipment,load_basis,unit):
    h=history(conn,exercise,equipment,load_basis,unit)
    valid=[r for r in h if r['form']=='good' and r['reps'] and r['load'] is not None and not r['pain'] and r['status']=='completed']
    if not valid:
        return {'exercise':exercise,'unit':unit,'best_load':None,'best_reps_at_best_load':None,'estimated_1rm':None,'note':'No clean, comparable sets yet.'}
    best=max(r['load'] for r in valid)
    reps=max(r['reps'] for r in valid if r['load']==best)
    # Epley only for hard sets 1..10 reps, near-max effort; never label this a tested maximum
    close=[r for r in valid if 1<=r['reps']<=10 and r['rir'] is not None and r['rir']<=1]
    e1rm=round(max(r['load']*(1+r['reps']/30) for r in close),2) if close else None
    return {'exercise':exercise,'equipment':equipment,'load_basis':load_basis,'unit':unit,
            'best_load':best,'best_reps_at_best_load':reps,'estimated_1rm':e1rm,
            'note':'Best load/reps are historical clean sets; estimated 1RM is a rough formula estimate, not a tested maximum.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Offline private training history and progressive overload engine')
    p.add_argument('--db',required=True,help='Local SQLite DB file (NEVER commit user data)')
    s=p.add_subparsers(dest='command',required=True)
    s.add_parser('init')
    log=s.add_parser('log');log.add_argument('--input',required=True)
    for command in ('plan','pr'):
        z=s.add_parser(command)
        for key in ('exercise','equipment','load-basis'):
            z.add_argument('--'+key,required=True)
        z.add_argument('--unit',choices=['kg','lb'],default='kg')
        if command=='plan':
            z.add_argument('--rep-min',type=int,default=8);z.add_argument('--rep-max',type=int,default=12)
            z.add_argument('--sets',type=int,default=3);z.add_argument('--increment',type=float,default=2.5)
            z.add_argument('--readiness',choices=['normal','good','low','pain'],default='normal')
            z.add_argument('--rest-seconds',type=int,default=120)
            z.add_argument('--eccentric-seconds',type=float,default=2)
            z.add_argument('--concentric-seconds',type=float,default=1)
            z.add_argument('--save',action='store_true',help='Save proposed plan separately from actual sets')
    args=p.parse_args(argv)
    try:
        path=Path(args.db);path.parent.mkdir(parents=True,exist_ok=True)
        with connect(path) as conn:
            if args.command=='init':
                result={'database':str(path),'status':'initialized','private':True}
            elif args.command=='log':
                with open(args.input,encoding='utf-8') as f:doc=json.load(f)
                result={'session_id':add_session(conn,doc),'status':'logged','note':'Only reported actual sets; no plans counted.'}
            elif args.command=='plan':
                result=prescribe(conn,args.exercise,args.equipment,args.load_basis,args.unit,args.rep_min,args.rep_max,args.sets,args.increment,args.readiness,args.rest_seconds,args.eccentric_seconds,args.concentric_seconds,args.save)
            else:
                result=personal_records(conn,args.exercise,args.equipment,args.load_basis,args.unit)
            print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,sqlite3.Error,FileNotFoundError,json.JSONDecodeError) as exc:
        p.exit(2,'Error: '+str(exc)+'\n')

if __name__=='__main__':
    main()
