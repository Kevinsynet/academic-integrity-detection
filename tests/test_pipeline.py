import json
from pathlib import Path
from src.pipeline import run_pipeline
from src.config import Config

def test_pipeline_json_and_self_exclusion(tmp_path):
 import pymupdf as fitz
 inp=tmp_path/'in';inp.mkdir();out=tmp_path/'out'
 for name in ('one','two'):
  d=fitz.open();p=d.new_page();p.insert_textbox((40,40,500,700),'The neighborhood garden residents shared tools and organized weekly watering shifts, improving community access to fresh vegetables and distributing work fairly.');d.save(inp/f'{name}.pdf');d.close()
 reports,_=run_pipeline(inp,out,Config(threshold=.5,chunk_size=40,overlap=5),tmp_path/'refs',skip_video=True)
 assert len(reports)==2 and all(r['peer_matches'] for r in reports)
 for r in reports:
  saved=json.loads((out/f"{r['document_id']}.json").read_text());assert saved['document_id']==r['document_id']
  assert all(x['matched_document']!=r['document_id'] for x in r['peer_matches'])
  assert any(x['match_category']=='exact-copy' for x in r['peer_matches'])
  assert saved['processing_metadata']['risk_thresholds']=={'medium':10.0,'high':25.0}

def test_both_ground_truth_paraphrase_pairs_are_detected(tmp_path):
 from pathlib import Path
 import shutil
 from src.embeddings import Embedder
 from src.pipeline import run_pipeline
 from src.config import Config

 embedder=Embedder(device='cpu')
 if embedder.fallback:
  import pytest
  pytest.skip('requires the primary MiniLM model to verify semantic paraphrases')
 root=Path(__file__).resolve().parents[1]
 inp=tmp_path/'paraphrase-input';inp.mkdir();out=tmp_path/'paraphrase-reports'
 files=['garden_original.pdf','coastal_paraphrase.pdf','garden_paraphrase.docx']
 for name in files:
  source=next(root.rglob(name));shutil.copy2(source,inp/name)
 reports,_=run_pipeline(inp,out,Config(threshold=.60),tmp_path/'no-references',skip_video=True)
 by_id={report['document_id']:report for report in reports}
 for target in ('coastal_paraphrase','garden_paraphrase'):
  matches=by_id['garden_original']['peer_matches']
  assert any(match['matched_document']==target for match in matches)

def test_pdf_to_spoken_mp4_cross_modal_match(tmp_path):
 from pathlib import Path
 import shutil
 from src.pipeline import run_pipeline
 from src.config import Config
 root=Path(__file__).resolve().parents[1]
 inp=tmp_path/'crossmodal-input';inp.mkdir();out=tmp_path/'crossmodal-reports'
 for source in (root/'sample_submissions/pdf/garden_original.pdf',root/'sample_submissions/video/garden_spoken.mp4'):
  shutil.copy2(source,inp/source.name)
 reports,_=run_pipeline(inp,out,Config(threshold=.60),tmp_path/'empty-reference',skip_video=False)
 by_id={report['document_id']:report for report in reports}
 assert by_id['garden_spoken']['processing_metadata']['transcription_status']=='transcribed'
 assert any(match['matched_document']=='garden_spoken' for match in by_id['garden_original']['multimodal_matches'])
