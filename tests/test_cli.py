from src.extractors import extract_document
from run_integrity_check import main

def test_cli_end_to_end(tmp_path):
 import pymupdf as fitz
 inp=tmp_path/'in';inp.mkdir();out=tmp_path/'out'
 d=fitz.open();p=d.new_page();p.insert_text((72,72),'A fictional observation about a neighborhood garden and weekly community watering schedule.');d.save(inp/'sample.pdf');d.close()
 (inp/'unsupported.txt').write_text('This file type should be skipped and reported.')
 (inp/'corrupted.pdf').write_bytes(b'not a valid pdf')
 assert main(['--input_dir',str(inp),'--output_dir',str(out),'--reference_dir',str(tmp_path/'refs'),'--risk_medium','12','--risk_high','40','--skip_video'])==0
 assert (out/'sample.json').exists() and (out/'sample.md').exists() and (out/'aggregate_summary.json').exists()
 import json
 report=json.loads((out/'sample.json').read_text())
 assert {'document_id','filename','extraction_status','total_integrity_risk','scores','peer_matches','multimodal_matches','external_matches','ai_analysis','explanations','warnings','processing_metadata'} <= report.keys()
 assert {'peer_similarity_percentage','external_similarity_percentage','ai_generated_probability'} <= report['scores'].keys()
 assert report['processing_metadata']['risk_thresholds']=={'medium':12.0,'high':40.0}
 aggregate=json.loads((out/'aggregate_summary.json').read_text())
 assert aggregate['processing_counts']['skipped_unsupported']==1
 assert aggregate['processing_counts']['failed_extraction']==1
 assert (out/'corrupted.json').exists()
 assert aggregate['skipped_files'][0].endswith('unsupported.txt')
 assert (out/'similarity_matrix.csv').exists() and (out/'aggregate_summary.md').exists()
