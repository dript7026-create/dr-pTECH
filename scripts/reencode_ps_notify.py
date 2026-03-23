from pathlib import Path
p=Path('readAIpolish/ps_notify.ps1')
s=p.read_text(encoding='utf-8-sig')
p.write_text(s, encoding='utf-8')
print('rewrote without BOM')
