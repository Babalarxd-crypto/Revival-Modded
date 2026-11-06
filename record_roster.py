"""Observe normal game's lobby from before login; never redirect or write packets."""
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import frida
from capture_live_difficulty import JS

HERE = Path(__file__).resolve().parent


def main():
    print('KADRO KAYDI: Offline oyunu kapat. Normal oyunu henuz acma.', flush=True)
    device = frida.get_local_device()
    if any(p.name.lower() == 'binarytru.exe' for p in device.enumerate_processes()):
        raise RuntimeError('Oyun zaten acik. Kapatip kaydi yeniden baslat; kadro giriste gelir.')
    print('Simdi NORMAL launcher ile oyunu ac. Kayit hazir mesaji gelmeden giris yapma.', flush=True)
    deadline = time.monotonic() + 600
    game = None
    while time.monotonic() < deadline:
        games = [p for p in device.enumerate_processes() if p.name.lower() == 'binarytru.exe']
        if len(games) > 1:
            raise RuntimeError('Birden fazla oyun acik')
        if games:
            game = games[0]; break
        time.sleep(.15)
    if game is None:
        raise RuntimeError('10 dakika icinde oyun acilmadi; oyun baslatilmadi/kapatilmadi.')
    path = HERE / f'capture-roster-{datetime.now():%Y%m%d-%H%M%S-%f}.log'
    lock = threading.Lock()
    session = device.attach(game.pid)
    try:
        with path.open('x', encoding='utf-8') as out:
            started = time.monotonic()
            def write(text):
                with lock:
                    out.write(f'{time.monotonic()-started:.6f} {text}\n')
                    out.flush()
            def message(msg, data):
                if msg['type'] != 'send':
                    write('HOOK_ERROR ' + json.dumps(msg)); return
                p = msg['payload']
                if p.get('kind') == 'data':
                    write(f"[8001 {p['direction']}] {p['size']}B {p['hex']}")
                else:
                    write('EVENT ' + json.dumps(p))
                    print(p, flush=True)
            script = session.create_script(JS)
            script.on('message', message)
            script.load()
            try:
                root = tk.Tk()
                root.title('Normal oyundan kadro kaydi')
                body = ttk.Frame(root, padding=20)
                body.pack(fill='both', expand=True)
                ttk.Label(body, text='Kayit acik. Normal oyunda giris yap, kadronun yuklenmesini bekle.\n'
                          'Satin alma, odul veya kadro onayi yapma.\n'
                          'Bitirince asagidaki dugmeye bas; oyun acik kalir.', wraplength=550).pack()
                ttk.Button(body, text='KAYDI BITIR VE KONTROL ET', command=root.destroy).pack(pady=15)
                root.mainloop()
            finally:
                script.unload()
    finally:
        session.detach()
    from roster_menu import inspect
    try:
        inspect(path)
    except (ValueError, OSError, AssertionError) as exc:
        print(f'Kayit saklandi ama kadro dogrulanamadi: {exc}\n{path}', flush=True)
    else:
        print(f'Kadro kaydi hazir: {path}\nLauncher > Kadro kaydi ac ile sec.', flush=True)
        print('Bu lobi kaydidir; tek basina mac kaydi degildir.', flush=True)
    input('Kapatmak icin Enter: ')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Kayit durdu: {exc}', flush=True)
        input('Kapatmak icin Enter: ')
        raise SystemExit(1)
