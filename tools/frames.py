"""Визуальный контроль анимации.

Запуск из корня проекта:  python tools/frames.py
Результат в qa/:
  desktop_tX.XX.png  — кадры анимации (стейдж 1280x691) в ключевые моменты
  mobile.png         — финальный кадр на ширине 390px
  sheet.png          — контактный лист всех кадров
  report.txt         — метрики: сходство финала с reference.jpg, горизонтальный скролл
"""
import functools, http.server, threading, pathlib
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
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.wait_for_function('typeof tl !== "undefined"')
        pg.evaluate('document.fonts.ready.then(() => 1)')
        # стейдж ровно 1280px, чтобы кадры сравнивались с reference пиксель в пиксель
        pg.add_style_tag(content='.wrap{max-width:none!important;padding:0!important}.frame{width:1280px!important;border-radius:0!important}')
        pg.evaluate('fit(); tl.pause(); 0')  # не возвращать объект таймлайна: его сериализация роняет вкладку
        for t in TIMES:
            pg.evaluate(f'tl.time({t if t is not None else "tl.duration()"}); 0')
            name = QA / f'desktop_t{(t if t is not None else 99):.2f}.png'
            pg.locator('#frame').screenshot(path=str(name))
            shots.append(name)

        ref = np.asarray(Image.open(ROOT / 'reference.jpg').convert('RGB'), dtype=np.float32)
        fin = np.asarray(Image.open(shots[-1]).convert('RGB').resize((ref.shape[1], ref.shape[0])), dtype=np.float32)
        d = np.abs(ref - fin).mean(axis=2)
        env = d[140:430, 420:850]  # зона конверта и печати
        report.append(f'final vs reference: mean diff all={d.mean():.2f}  envelope={env.mean():.2f}  (норма < 6)')
        Image.fromarray(np.clip(d * 4, 0, 255).astype(np.uint8)).save(QA / 'diff_final.png')

        m = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        m.goto(f'http://127.0.0.1:{PORT}/index.html')
        m.wait_for_function('typeof tl !== "undefined"')
        m.evaluate('tl.progress(1); 0')
        m.screenshot(path=str(QA / 'mobile.png'))
        hs = m.evaluate('document.documentElement.scrollWidth > innerWidth')
        report.append(f'mobile 390px horizontal scroll: {"ЕСТЬ — ошибка" if hs else "нет"}')
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
