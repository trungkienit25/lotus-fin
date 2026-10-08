"""TEST_ONLY_POLICY proof obligations; not a production rule engine.

Numbers are arbitrary boundary markers, never suggested business thresholds.
The proposed comparator and precedence remain subject to Chat approval.
"""
import json
from decimal import Decimal
from pathlib import Path

cases = []
warning, high = Decimal('10'), Decimal('20')
for name, threshold in [('T_warning', warning), ('T_high', high),
                        ('A_min', Decimal('100')), ('D_min', Decimal('200')), ('N_min', Decimal('3'))]:
    step = Decimal('1') if name == 'N_min' else Decimal('0.000000001')
    for relation, value, expected in [('below', threshold-step, False), ('equal', threshold, True),
                                      ('above', threshold+step, True)]:
        cases.append({'case':name+'_'+relation, 'expected':expected,
                      'actual':value >= threshold, 'value':str(value), 'threshold':str(threshold)})
for value, expected in [('9.999999999', None), ('10', 'WARNING'), ('19.999999999', 'WARNING'), ('20', 'HIGH'), ('20.000000001', 'HIGH')]:
    d = Decimal(value)
    # Declarative boundary facts; neither rule policies nor source access exist.
    actual = 'HIGH' if d >= high else ('WARNING' if d >= warning else None)
    cases.append({'case':'ORDER_'+value, 'expected':expected, 'actual':actual})
cases.append({'case':'NO_ROUND_BEFORE_THRESHOLD', 'expected':False,
              'actual':Decimal('9.999999999') >= warning})
precedence = ['FORBIDDEN','SOURCE_INVALID','NOT_APPLICABLE','POLICY_PENDING','EVALUABLE']
for earlier,later in zip(precedence,precedence[1:]):
    cases.append({'case':earlier+'_BEFORE_'+later,'expected':True,
                  'actual':precedence.index(earlier) < precedence.index(later)})
for c in cases: c['result']='PASS' if c['actual']==c['expected'] else 'FAIL'
out={'evidence_kind':'SPECIFICATION_ONLY','policy_scope':'TEST_ONLY_POLICY',
     'production_approved':False,'comparator_approved':False,'production_finding':None,
     'production_severity':None,'cases':cases,'count':len(cases),
     'passed':sum(c['result']=='PASS' for c in cases)}
Path(__file__).with_name('AI003_FINAL_SYMBOLIC_RESULTS_2026-09-30.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'count':out['count'],'passed':out['passed'],'scope':out['policy_scope']}))
