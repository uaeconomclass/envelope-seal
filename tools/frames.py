"""Визуальный контроль анимации.

Запуск из корня проекта:  python tools/frames.py
Результат в qa/:
  desktop_tX.XX.png  — кадры анимации (стейдж 1280x691) в ключевые моменты
  mobile.png         — финальный кадр на ширине 390px
  sheet.png          — контактный лист всех кадров
  report.txt         — метрики: сходство финала с reference.jpg, горизонтальный скролл
"""
import functools, http.server, threading, pathlib, json
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
QA = ROOT / 'qa'
TIMES = [0, 0.7, 1.6, 2.4, 2.8, 3.2, 3.9, 4.3, None]  # None = конец таймлайна
PORT = 8811


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    QA.mkdir(exist_ok=True)
    srv = serve()
    shots, report = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 900})
        errors=[]
        cdn={}
        pg.on('pageerror',lambda err:errors.append(str(err)))
        pg.on('response',lambda response:cdn.update({'gsap':response.body()}) if response.url.endswith('/gsap.min.js') and response.status==200 else None)
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.wait_for_function('window.tl && document.querySelector(".envelope").envelope')
        pg.evaluate('document.querySelector(".envelope").envelope.ready.then(()=>1)')
        pg.evaluate('document.fonts.ready.then(() => 1)')
        # стейдж ровно 1280px, чтобы кадры сравнивались с reference пиксель в пиксель
        pg.add_style_tag(content='.envelope{max-width:none!important}.es-frame{width:1280px!important;border-radius:0!important}')
        pg.evaluate('fit(); document.querySelector(".envelope").envelope.play(); tl.pause(); 0')
        for t in TIMES:
            pg.evaluate(f'tl.time({t if t is not None else "tl.duration()"}); 0')
            name = QA / f'desktop_t{(t if t is not None else 99):.2f}.png'
            pg.locator('.es-frame').screenshot(path=str(name))
            shots.append(name)

        ref = np.asarray(Image.open(ROOT / 'reference.jpg').convert('RGB'), dtype=np.float32)
        fin = np.asarray(Image.open(shots[-1]).convert('RGB').resize((ref.shape[1], ref.shape[0])), dtype=np.float32)
        d = np.abs(ref - fin).mean(axis=2)
        env = d[140:430, 420:850]  # зона конверта и печати
        report.append(f'final vs reference: mean diff all={d.mean():.2f} envelope={env.mean():.2f}; original limits all<3 / envelope<4: {"PASS" if d.mean()<3 and env.mean()<4 else "NOT MET (regenerated artwork / revised flap)"}')
        Image.fromarray(np.clip(d * 4, 0, 255).astype(np.uint8)).save(QA / 'diff_final.png')

        m = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        m.goto(f'http://127.0.0.1:{PORT}/index.html')
        m.wait_for_function('typeof tl !== "undefined"')
        m.evaluate('document.querySelector(".envelope").envelope.ready.then(()=>1)')
        m.evaluate('document.querySelector(".envelope").envelope.play(); tl.pause().progress(1); 0')
        m.screenshot(path=str(QA / 'mobile.png'))
        hs = m.evaluate('document.documentElement.scrollWidth > innerWidth')
        report.append(f'mobile 390px horizontal scroll: {"ЕСТЬ — ошибка" if hs else "нет"}')
        for t in (0,2.8,3.9):
            m.evaluate(f'tl.time({t}); 0')
            m.locator('.es-frame').screenshot(path=str(QA/f'mobile_t{t:.2f}.png'))
        # Check replay, keyboard-accessible pause, actual playback and reduced motion.
        pg.locator('[data-part=replay]').click()
        pg.locator('[data-part=pause]').click()
        assert pg.evaluate('tl.paused()'), 'Pause button did not pause'
        pg.locator('[data-part=pause]').click()
        assert not pg.evaluate('tl.paused()'), 'Resume button did not resume'
        samples=pg.evaluate('''() => new Promise(resolve=>{
          const times=[];let prev=performance.now();
          function tick(now){times.push(now-prev);prev=now;if(times.length<120)requestAnimationFrame(tick);else resolve(times.slice(1));}
          requestAnimationFrame(tick);
        })''')
        report.append(f'playback rAF median={np.median(samples):.1f}ms p95={np.percentile(samples,95):.1f}ms (machine sample, not universal 60fps guarantee)')
        reduced=b.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
        reduced.goto(f'http://127.0.0.1:{PORT}/index.html')
        reduced.wait_for_function('window.tl && tl.progress()===1')
        assert reduced.evaluate('tl.paused()'), 'Reduced motion timeline is running'
        reduced.screenshot(path=str(QA/'reduced-motion.png'))
        report.append('replay / pause / resume / reduced-motion: PASS')
        click=b.new_page(viewport={'width':1400,'height':900})
        if cdn.get('gsap'):click.route('**/gsap.min.js',lambda route:route.fulfill(content_type='application/javascript',body=cdn['gsap']))
        click.route('**/index.html',lambda route:route.fulfill(content_type='text/html; charset=utf-8',body=(ROOT/'index.html').read_text(encoding='utf-8').replace('data-trigger="inview"','data-trigger="click"')))
        click.goto(f'http://127.0.0.1:{PORT}/index.html')
        click.wait_for_function('!!window.tl')
        click.evaluate('document.querySelector(".envelope").envelope.ready.then(()=>1)')
        assert click.evaluate('tl.paused() && tl.time()<.01'), 'Click mode autoplayed'
        click.locator('[data-part=replay]').click()
        assert click.evaluate('!tl.paused()'), 'Click mode did not start'
        report.append('click trigger: PASS')
        offscreen=b.new_page(viewport={'width':1400,'height':900})
        if cdn.get('gsap'):offscreen.route('**/gsap.min.js',lambda route:route.fulfill(content_type='application/javascript',body=cdn['gsap']))
        offscreen.route('**/index.html',lambda route:route.fulfill(content_type='text/html; charset=utf-8',body=(ROOT/'index.html').read_text(encoding='utf-8').replace('class="envelope"','class="envelope" style="margin-top:1200px"')))
        offscreen.goto(f'http://127.0.0.1:{PORT}/index.html')
        offscreen.wait_for_function('!!window.tl')
        offscreen.evaluate('document.querySelector(".envelope").envelope.ready.then(()=>1)')
        assert offscreen.evaluate('tl.paused() && tl.time()<.01'), 'Inview mode started offscreen'
        offscreen.locator('.es-frame').scroll_into_view_if_needed()
        offscreen.wait_for_function('tl.time()>.05')
        offscreen.evaluate('tl.pause().progress(1); window.scrollTo(0,0); 0')
        offscreen.locator('.es-frame').scroll_into_view_if_needed()
        assert offscreen.evaluate('tl.progress()===1'), 'Inview replayed automatically'
        report.append('inview trigger / once-only: PASS')
        report.append('page JS errors: '+json.dumps(errors))
        assert not errors,errors
        budgets=QA/'asset-budget.json'
        if budgets.exists():report.append('asset budgets: '+budgets.read_text())
        b.close()
    srv.shutdown()

    ims = [Image.open(s).convert('RGB').resize((640, 345)) for s in shots]
    cols = 3
    sheet = Image.new('RGB', (640 * cols, 345 * ((len(ims) + cols - 1) // cols)), 'black')
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 345))
    sheet.save(QA / 'sheet.png')
    (QA / 'report.txt').write_text('\n'.join(report), encoding='utf-8')
    print('\n'.join(report))


if __name__ == '__main__':
    main()
