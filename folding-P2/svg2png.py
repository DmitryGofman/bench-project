"""Render SVG drawings to PNG with the headless Chromium that ships in this environment."""
import sys, re, subprocess, glob, os
CH = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0]
for p in sys.argv[1:]:
    t = open(p).read(4000); w = int(float(re.search(r'width="([\d.]+)"', t).group(1))); h = int(float(re.search(r'height="([\d.]+)"', t).group(1)))
    out = os.path.splitext(p)[0] + '.png'
    subprocess.run([CH, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', f'--window-size={w+20},{h+140}',
                    f'--screenshot={out}', 'file://' + os.path.abspath(p)], capture_output=True, timeout=120)
    from PIL import Image
    im = Image.open(out); im.crop((0, 0, min(w, im.width), min(h, im.height))).save(out)
    print(out, im.size)
