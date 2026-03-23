import zipfile
from pathlib import Path
src = Path(r"C:\Users\rrcar\Documents\drIpTECH\drIpTECHBlenderPlug-Ins\TxTUR")
files = [src / 'blender_txtur_addon.py', src / 'blenderTxTUR.dll']
zip_path = src / 'TxTUR_addon_bundle.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        if f.exists():
            z.write(f, arcname=f.name)
        else:
            print('Missing:', f)
print('Created', zip_path)
