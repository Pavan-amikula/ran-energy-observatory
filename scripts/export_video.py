"""Convert the actual Chromium app recording to a compact MP4 and README GIF."""
from pathlib import Path
import subprocess
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]

def main():
    exe=imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([exe,'-y','-i',str(ROOT/'work'/'demo.webm'),'-vf','scale=1280:-2','-c:v','libx264','-crf','26','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'results'/'demo.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run([exe,'-y','-ss','2','-t','12','-i',str(ROOT/'results'/'demo.mp4'),'-vf','fps=8,scale=960:-2',str(ROOT/'results'/'demo.gif')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print('MP4 and README GIF exported from the browser recording')

if __name__=='__main__':main()
