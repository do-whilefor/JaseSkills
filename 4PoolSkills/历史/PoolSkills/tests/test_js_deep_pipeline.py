import json, tempfile, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from js.sourcemap_restorer import restore
from js.chunk_lineage_builder import build

class JsDeepPipelineTest(unittest.TestCase):
    def test_sourcemap_restores_sources_content_and_chunk_lineage_tracks_dynamic_import(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            (r/'app.js').write_text("import('./admin.js');\n//# sourceMappingURL=app.js.map\n",encoding='utf-8')
            (r/'admin.js').write_text("export const path='/admin';",encoding='utf-8')
            (r/'app.js.map').write_text(json.dumps({'version':3,'file':'app.js','sources':['src/app.ts'],'sourcesContent':["export const api='/api/admin'"],'mappings':''}),encoding='utf-8')
            sm=restore(js_file=r/'app.js', out_dir=r/'restored')
            self.assertEqual(sm['status'],'parsed')
            self.assertEqual(len(sm['restored_sources']),1)
            lin=build(r)
            self.assertEqual(lin['counts']['dynamic_imports'],1)
            self.assertTrue(any(e['type']=='dynamic_import' for e in lin['edges']))

if __name__=='__main__': unittest.main()
