from pathlib import Path
import pymupdf as fitz
from docx import Document
from src.extractors import extract_document

def test_pdf_and_docx_extraction(tmp_path):
 p=tmp_path/'x.pdf';d=fitz.open();page=d.new_page();page.insert_text((72,72),'hello pdf');d.save(p);d.close()
 out=extract_document(p);assert out['extraction_status']=='ok' and 'hello pdf' in out['extracted_text'] and out['source_segments'][0]['page']==1
 q=tmp_path/'y.docx';doc=Document();doc.add_paragraph('hello docx');doc.add_table(rows=1,cols=1).cell(0,0).text='table value';doc.save(q)
 out=extract_document(q);assert 'hello docx' in out['extracted_text'] and 'table value' in out['extracted_text']
def test_corrupt_pdf_is_reported(tmp_path):
 p=tmp_path/'bad.pdf';p.write_bytes(b'not pdf');out=extract_document(p);assert out['extraction_status']=='error' and out['warnings']

def test_invalid_extension_is_reported(tmp_path):
 p=tmp_path/'notes.txt';p.write_text('plain text is outside supported formats')
 result=extract_document(p)
 assert result['extraction_status']=='error'
 assert 'Unsupported file extension' in result['warnings'][0]

def test_empty_pdf_is_distinct_from_corrupt_pdf(tmp_path):
 path=tmp_path/'empty.pdf'
 pdf=fitz.open();pdf.new_page();pdf.save(path);pdf.close()
 result=extract_document(path)
 assert result['extraction_status']=='empty'
 assert 'No extractable text' in result['warnings'][0]

def test_generated_spoken_mp4_transcribes_with_timestamps():
 from pathlib import Path
 root=Path(__file__).resolve().parents[1]
 sample=root/'sample_submissions'/'video'/'garden_spoken.mp4'
 result=extract_document(sample,device='cpu')
 assert result['extraction_status']=='ok'
 assert result['metadata']['transcription_status']=='transcribed'
 assert result['metadata']['language']=='en'
 text=result['extracted_text'].lower()
 assert 'alderwick' in text and 'watering teams' in text and 'fresh food' in text
 assert result['source_segments']
 assert all(segment['end']>segment['start'] for segment in result['source_segments'])
 assert result['source_segments'][0]['start']==0.0
 assert 10 <= result['source_segments'][-1]['end'] <= 30

def test_second_generated_spoken_mp4_transcribes_with_timestamps():
 root=Path(__file__).resolve().parents[1]
 sample=root/'sample_submissions'/'video'/'original_river_spoken.mp4'
 result=extract_document(sample,device='cpu')
 assert result['extraction_status']=='ok'
 assert result['metadata']['transcription_status']=='transcribed'
 assert result['metadata']['language']=='en'
 text=result['extracted_text'].lower()
 assert 'river' in text and 'sampling kits' in text and 'watershed council' in text
 assert result['source_segments'] and all(seg['end']>seg['start'] for seg in result['source_segments'])
 assert 10 <= result['source_segments'][-1]['end'] <= 30
