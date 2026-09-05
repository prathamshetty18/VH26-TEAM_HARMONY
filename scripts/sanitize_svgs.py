import glob
import os
import xml.etree.ElementTree as ET

def sanitize_svgs():
    folders = ['src/static/diagrams', 'frontend/public/diagrams', 'frontend/public/static/diagrams']
    for folder in folders:
        files = glob.glob(os.path.join(folder, '*.svg'))
        for f in files:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Ensure standard XML declaration
            if not content.strip().startswith('<?xml'):
                content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content.strip()
            
            # Escape character entities safely
            content = content.replace('50µ', '50&#181;m')
            content = content.replace('10µ', '10&#181;m')
            content = content.replace('62.5 µs', '62.5 &#181;s')
            content = content.replace('20°C', '20&#176;C')
            content = content.replace('25°C', '25&#176;C')
            content = content.replace('115°C', '115&#176;C')
            content = content.replace('35-50°C', '35-50&#176;C')
            
            try:
                ET.fromstring(content)
                with open(f, 'w', encoding='utf-8') as out:
                    out.write(content)
                print(f"[OK] {f}")
            except Exception as e:
                print(f"[ERR] {f}: {e}")

if __name__ == '__main__':
    sanitize_svgs()
