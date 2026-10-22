"""Use the exact embeddable block for the local demo; no divergent timeline."""
from pathlib import Path
root=Path(__file__).resolve().parent.parent
fragment=(root/'dist/envelope.html').read_text(encoding='utf-8')
fragment=fragment.replace('href="envelope.css"','href="dist/envelope.css"').replace('src="envelope.js"','src="dist/envelope.js"').replace('src="assets/','src="dist/assets/')
head='''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Запечатываем ваше письмо</title><style>html,body{margin:0;background:#0b1020}body{min-width:280px}</style></head><body>
'''
debug='''<script>
document.addEventListener('envelope:ready',e=>{window.tl=e.target.envelope.timeline;window.fit=e.target.envelope.fit;});
</script></body></html>'''
(root/'index.html').write_text(head+fragment+debug,encoding='utf-8')
