from src.ai_detector import analyze_ai
from src.extractors import extract_document

def test_ai_short_and_silent_video(tmp_path):
 assert analyze_ai('too short')['ai_generated_probability']==0
 # Silence is detected before Whisper is initialized, so no speech is falsely reported.
 import subprocess
 p=tmp_path/'silent.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=black:s=160x120:r=5','-f','lavfi','-i','anullsrc=r=16000:cl=mono','-t','1','-c:v','libx264','-c:a','aac',str(p)],check=True)
 out=extract_document(p);assert out['extraction_status']=='empty' and out['metadata']['transcription_status']=='silent' and out['warnings']

def test_mp4_without_audio_is_reported(tmp_path):
 import subprocess
 p=tmp_path/'no_audio.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=black:s=160x120:r=5','-t','1','-c:v','libx264',str(p)],check=True)
 out=extract_document(p)
 assert out['extraction_status']=='error' and any('audio' in w.lower() or 'ffmpeg' in w.lower() for w in out['warnings'])
