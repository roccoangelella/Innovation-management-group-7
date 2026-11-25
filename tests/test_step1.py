import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from step1_landscape import fractional, volume, parse_cpc, analyze, digest

CFG=json.loads((Path(__file__).resolve().parents[1]/"config/step1.json").read_text())
class TestStep1(unittest.TestCase):
    def test_fractional(self):
        u=pd.DataFrame({"id":[1,2,3],"year":[2020,2020,2020]})
        links=pd.DataFrame({"id":[1,1,1,2],"c":["A","A","B",None]})
        t=fractional(u,links,"id","c").set_index("c").n_frac
        self.assertAlmostEqual(t.sum(),3)
        self.assertAlmostEqual(t["A"],.5)
        self.assertAlmostEqual(t["Unknown"],2)
    def test_person_weight(self):
        u=pd.DataFrame({"id":[1],"year":[2020]})
        links=pd.DataFrame({"id":[1,1,1,1],"c":["IT","IT","DE",None],"person":[1,1,2,3]})
        t=fractional(u,links,"id","c",entity="person").set_index("c").n_frac
        self.assertAlmostEqual(t["IT"],1/3)
        self.assertAlmostEqual(t["Unknown"],1/3)
    def test_weighted(self):
        u=pd.DataFrame({"id":[1,2],"year":[2020,2020]})
        t=fractional(u,pd.DataFrame({"id":[1,1,1],"c":["A","A","B"],"w":[.2,.3,.5]}),"id","c",weight="w")
        self.assertAlmostEqual(t.n_frac.sum(),2)
    def test_truncation_and_zero(self):
        f=pd.DataFrame({"year":[2001,2022,2023]})
        v=volume(f,CFG)
        self.assertEqual(v.loc[2023,"n"],1)
        self.assertTrue(np.isnan(v.loc[2023,"yoy_pct"]))
        self.assertTrue(np.isnan(v.loc[2001,"yoy_pct"]))
        self.assertEqual(v.loc[2002,"n"],0)
    def test_cpc(self):
        self.assertEqual(parse_cpc(pd.Series(["B25J 9/16","G06N 3/00","invalid"])).tolist()[:2],["B25J","G06N"])
    def test_preview_and_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); src=root/"source.csv"
            pd.DataFrame({"docdb_family_id":["1","2","3"],"year":[2000,2020,2023],"model_decision":[1,1,1],"source_query":["a","b","b"]}).to_csv(src,index=False)
            preview=analyze(src,root/"preview",CFG)
            self.assertEqual(preview["family_in_window"],3)
            self.assertFalse((root/"preview/family_cpc_annual.csv").exists())
            folder=root/"meta";folder.mkdir()
            data={
                "applications":pd.DataFrame({"docdb_family_id":["1","1","2"],"appln_id":["11","12","21"],"appln_auth":["US","WO","CN"],"appln_kind":["A","W","A"],"appln_filing_year":[2002,2003,2020],"earliest_filing_year":[2000,2000,2020]}),
                "cpc":pd.DataFrame({"appln_id":["11","12","21"],"cpc_class_symbol":["B25J 9/16","G06N 3/00","B25J 9/16"]}),
                "persons":pd.DataFrame({"appln_id":["11","12"],"person_id":["101","101"],"country":["US","US"],"applt_seq_nr":[1,1],"invt_seq_nr":[0,1]}),
                "wipo":pd.DataFrame({"appln_id":["11","12"],"techn_field_nr":[1,1],"weight":[1.,1.]}),
                "wipo_names":pd.DataFrame({"techn_field_nr":[1],"techn_field":["Field"],"techn_sector":["Sector"]}),
                "global_families":pd.DataFrame({"year":list(range(2000,2027)),"n":[10]*27}),
                "global_applications":pd.DataFrame({"year":list(range(2000,2027)),"n":[20]*27})}
            for name,df in data.items(): df.to_csv(folder/(name+".csv"),index=False)
            (folder/"manifest.json").write_text(json.dumps({"input_sha256":digest(src),"config":CFG,"environment":"TEST","edition":"synthetic","counts":{n:len(d) for n,d in data.items()},"sha256":{n:digest(folder/(n+".csv")) for n in data}}))
            report=analyze(src,root/"complete",CFG,folder)
            self.assertEqual(report["no_PI_application"],1)
            c=pd.read_csv(root/"complete/family_cpc_annual.csv")
            self.assertAlmostEqual(c.n_frac.sum(),2)
            v=pd.read_csv(root/"complete/application_annual.csv")
            self.assertEqual(v.n.sum(),3)
            t=pd.read_csv(root/"complete/family_applicant_annual.csv")
            self.assertAlmostEqual(t.n_frac.sum(),2)
            self.assertIn("Unknown",t.country.values)
if __name__=="__main__": unittest.main()
