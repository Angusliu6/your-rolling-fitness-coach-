import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('progression_db',ROOT/'scripts'/'progression_db.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def doc(reps=(10,10,10),rir=(2,2,2),load=25,equipment='machine-A',form='good',pain=False,status='completed',failure_last=False):
    return {'date':'2026-10-24','status':status,'pain':pain,'exercises':[{'exercise':'chest press','equipment':equipment,'load_basis':'machine_stack','unit':'kg','sets':[{'load':load,'reps':r,'rir':q,'form':form,'failure':failure_last and i==len(reps)-1} for i,(r,q) in enumerate(zip(reps,rir))]}]}

class ProgressionTest(unittest.TestCase):
    def setUp(self):
        self.c=m.connect(':memory:')
        self.q=lambda **kw:m.prescribe(self.c,'chest press','machine-A','machine_stack','kg',rep_min=8,rep_max=12,**kw)
    def tearDown(self):self.c.close()
    def test_baseline_no_fake_load(self):
        r=self.q();self.assertEqual(r['decision'],'baseline');self.assertIsNone(r['sets'][0]['load'])
    def test_hold_progress_reps(self):
        m.add_session(self.c,doc(reps=(12,11,9)));r=self.q();self.assertEqual(r['decision'],'repeat');self.assertEqual([x['reps_target'] for x in r['sets']],[12,12,10])
    def test_progress_only_at_top_with_rir(self):
        m.add_session(self.c,doc(reps=(12,12,12)));r=self.q();self.assertEqual(r['decision'],'increase');self.assertEqual(r['sets'][0]['load'],27.5)
    def test_failure_at_top_does_not_add_weight(self):
        m.add_session(self.c,doc(reps=(12,12,12),rir=(1,1,0),failure_last=True));self.assertNotEqual(self.q()['decision'],'increase')
    def test_fatigue_reduce_sets(self):
        m.add_session(self.c,doc());r=self.q(readiness='low');self.assertEqual(r['decision'],'recover');self.assertEqual(len(r['sets']),2)
    def test_early_failure_reduce_load(self):
        m.add_session(self.c,doc(reps=(9,8,6),rir=(1,0,0),failure_last=True));r=self.q();self.assertEqual(r['decision'],'reduce');self.assertEqual(r['sets'][0]['load'],22.5)
    def test_unknown_form_no_increase(self):
        m.add_session(self.c,doc(reps=(12,12,12),form='unknown'));self.assertEqual(self.q()['decision'],'verify')
    def test_partial_session_no_increase(self):
        m.add_session(self.c,doc(reps=(12,12,12),status='partial'));self.assertEqual(self.q()['decision'],'verify')
    def test_equipment_not_mixed(self):
        m.add_session(self.c,doc(reps=(12,12,12),equipment='machine-B'));self.assertEqual(self.q()['decision'],'baseline')
    def test_pr_not_estimate_without_rir(self):
        m.add_session(self.c,doc(reps=(12,12,12)));r=m.personal_records(self.c,'chest press','machine-A','machine_stack','kg');self.assertEqual(r['best_load'],25);self.assertIsNone(r['estimated_1rm'])
    def test_rir_one_estimate(self):
        m.add_session(self.c,doc(reps=(10,9,8),rir=(1,1,1)));r=m.personal_records(self.c,'chest press','machine-A','machine_stack','kg');self.assertIsNotNone(r['estimated_1rm'])
    def test_pain_stops(self):
        m.add_session(self.c,doc());r=self.q(readiness='pain');self.assertEqual(r['decision'],'stop');self.assertEqual(len(r['sets']),0)
    def test_warmups_excluded(self):
        d=doc(reps=(8,),rir=(2,));d['exercises'][0]['sets'].insert(0,{'kind':'warmup','load':10,'reps':15});m.add_session(self.c,d);r=self.q();self.assertEqual(len(r['last_sets']),1)
    def test_prescription_is_not_actual(self):
        self.q(save=True);self.assertEqual(len(m.history(self.c,'chest press','machine-A','machine_stack','kg')),0)
    def test_invalid_missing_unit(self):
        d=doc();d['exercises'][0]['unit']='';self.assertRaises(ValueError,m.add_session,self.c,d)

if __name__=='__main__':unittest.main()
