"""VargaMesh MiniPool – GUI-first native VMESH-only SOLO pool.

Run: python main.py             Windows / Linux desktop GUI
     python main.py --headless  Headless Linux server mode
"""
import argparse
import json
import logging
import os
import queue
import socket
import ipaddress
import pathlib
import signal
import subprocess
import sys
import threading
import time
import webbrowser

from minipool import __version__
from minipool.dashboard import start_dashboard
from minipool.service import PoolState
from minipool.rpc import VMeshRPC, RPCError
from minipool.node_installer import install_windows_core, InstallError, CORE_VERSION

BASE = pathlib.Path(getattr(sys, '_MEIPASS', pathlib.Path(__file__).resolve().parent))
APP_HOME = pathlib.Path(os.getenv('APPDATA') or os.getenv('XDG_CONFIG_HOME') or (pathlib.Path.home()/'.config'))/'VargaMeshMiniPool'
CONFIG_FILE = APP_HOME/'config.json'
DEFAULT_CHAIN = pathlib.Path(os.getenv('LOCALAPPDATA') or (pathlib.Path.home()/'.local/share'))/'VargaMeshMiniPool'/'chain'


def default_config():
    return {'node':{'binary':'','data_dir':str(DEFAULT_CHAIN),'cookie_path':str(DEFAULT_CHAIN/'.cookie'),'rpc_port':29667},
            'pool':{'bind':'0.0.0.0','stratum_port':3938,'dashboard_port':8686,
                    'share_difficulty':1024,'refresh_seconds':12}}


def load_config():
    if not CONFIG_FILE.exists(): return default_config()
    with CONFIG_FILE.open(encoding='utf-8') as f: conf=json.load(f)
    assert isinstance(conf,dict) and isinstance(conf.get('node'),dict) and isinstance(conf.get('pool'),dict)
    return conf


def save_config(conf):
    APP_HOME.mkdir(parents=True,exist_ok=True)
    temporary=CONFIG_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(conf,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary,CONFIG_FILE)

class Runtime:
    def __init__(self,conf):
        self.config=conf
        self.pool=None
        self.dashboard=None
        self.node_process=None
        self.node_owned=False

    def start_pool(self):
        if self.pool: return
        p=PoolState(self.config)
        try:
            p.start()
            dashboard=start_dashboard(p,self.config['pool']['dashboard_port'],BASE/'web')
        except Exception:
            p.close()
            raise
        self.pool=p
        self.dashboard=dashboard

    def stop_pool(self):
        if self.dashboard:
            self.dashboard.shutdown();self.dashboard.server_close()
            self.dashboard=None
        if self.pool:
            self.pool.close(); self.pool=None

    def node_info(self):
        info=VMeshRPC(self.config['node']['cookie_path'],self.config['node']['rpc_port'],timeout=3).call('getblockchaininfo')
        if info.get('chain') not in ('main','mainnet'):
            raise RPCError('Refusing to use a node outside VargaMesh mainnet.')
        return info

    def start_node(self):
        try:
            self.node_info()
            return 'Already running'
        except RPCError as error:
            if 'outside VargaMesh mainnet' in str(error):raise
        if self.node_process and self.node_process.poll() is None:return 'Starting'
        conf=self.config['node']
        binary=pathlib.Path(conf['binary']).expanduser()
        if not binary.is_file():raise RuntimeError('Official VargaMesh Core executable is missing.')
        directory=pathlib.Path(conf['data_dir']).expanduser()
        directory.mkdir(parents=True,exist_ok=True)
        argv=[str(binary),f'-datadir={directory}','-server=1','-listen=1',
              '-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1',
              f"-rpcport={int(conf['rpc_port'])}",'-port=29666']
        kw={}
        if os.name=='nt':kw['creationflags']=getattr(subprocess,'CREATE_NO_WINDOW',0)
        self.node_process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**kw)
        self.node_owned=True
        return 'Launched'

    def stop_node(self):
        if not self.node_owned or not self.node_process:return
        if self.node_process.poll() is None:
            try:
                VMeshRPC(self.config['node']['cookie_path'],self.config['node']['rpc_port'],timeout=5).call('stop')
                self.node_process.wait(timeout=30)
            except Exception as error:
                logging.warning('Node is still stopping: %s',error)
                return  # never kill an active database process
        self.node_process=None
        self.node_owned=False

    def shutdown(self):
        self.stop_pool()
        self.stop_node()


def headless(runtime):
    stop=threading.Event()
    def signal_handler(signum,frame):stop.set()
    for s in (signal.SIGTERM,signal.SIGINT):signal.signal(s,signal_handler)
    runtime.start_pool()
    logging.info('MiniPool dashboard: http://127.0.0.1:%s',runtime.config['pool']['dashboard_port'])
    while not stop.wait(1): pass
    runtime.shutdown()


def gui(runtime):
    import tkinter as tk
    from tkinter import filedialog,messagebox,ttk
    root=tk.Tk()
    root.title('VargaMesh MiniPool  •  VMESH SOLO')
    root.geometry('800x650')
    root.minsize(640,570)
    root.configure(bg='#0b1220')
    style=ttk.Style(root)
    try:style.theme_use('clam')
    except tk.TclError:pass
    style.configure('TFrame',background='#0b1220')
    style.configure('TLabel',background='#0b1220',foreground='#dbeafe',font=('Segoe UI',10))
    style.configure('Hint.TLabel',foreground='#93a4bd',background='#0b1220')
    style.configure('Title.TLabel',foreground='#ffffff',background='#0b1220',font=('Segoe UI',19,'bold'))
    style.configure('TButton',font=('Segoe UI',10),padding=(12,8))
    style.configure('TEntry',padding=7)
    frame=ttk.Frame(root,padding=22); frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='VargaMesh MiniPool',style='Title.TLabel').pack(anchor='w')
    ttk.Label(frame,text='Self-hosted VMESH SOLO  ·  SHA-256d  ·  VargaMesh Core  ·  1% developer fee',style='Hint.TLabel').pack(anchor='w',pady=(3,16))
    vars={
        'binary':tk.StringVar(value=runtime.config['node'].get('binary','')),
        'data_dir':tk.StringVar(value=runtime.config['node'].get('data_dir','')),
        'stratum_port':tk.StringVar(value=str(runtime.config['pool'].get('stratum_port',3938))),
        'dashboard_port':tk.StringVar(value=str(runtime.config['pool'].get('dashboard_port',8686))),
        'share_difficulty':tk.StringVar(value=str(runtime.config['pool'].get('share_difficulty',1024)))
    }
    def row(label,name,command=None):
        r=ttk.Frame(frame);r.pack(fill='x',pady=5)
        ttk.Label(r,text=label,width=22).pack(side='left')
        ent=ttk.Entry(r,textvariable=vars[name]);ent.pack(side='left',fill='x',expand=True,padx=7)
        if command:ttk.Button(r,text='Browse',command=command).pack(side='right')
    row('VargaMesh Node (.exe)','binary',lambda:vars['binary'].set(filedialog.askopenfilename(title='Select official vargameshd executable',filetypes=[('Programs','*.exe *'),('All','*')]) or vars['binary'].get()))
    row('Blockchain data folder','data_dir',lambda:vars['data_dir'].set(filedialog.askdirectory(title='VargaMesh data directory') or vars['data_dir'].get()))
    row('Stratum port','stratum_port')
    row('Dashboard port','dashboard_port')
    row('Share difficulty','share_difficulty')
    ttk.Label(frame,text='Every miner logs in with its own VMESH wallet address (vm1...).',style='Hint.TLabel').pack(anchor='w',pady=(10,2))
    ttk.Label(frame,text='RPC remains on 127.0.0.1. Stratum is available on the local network.',style='Hint.TLabel').pack(anchor='w')
    node_status=tk.StringVar(value='Node: not started by MiniPool')
    pool_status=tk.StringVar(value='Pool: stopped')
    ttk.Label(frame,textvariable=node_status).pack(anchor='w',pady=(18,3))
    ttk.Label(frame,textvariable=pool_status).pack(anchor='w',pady=(0,12))
    def apply():
        try:
            if runtime.pool: raise RuntimeError('Stop the pool before changing settings.')
            ports={k:int(vars[k].get()) for k in ('stratum_port','dashboard_port','share_difficulty')}
            if any(not 1<=ports[k]<=65535 for k in ('stratum_port','dashboard_port')):raise ValueError('Invalid port')
            if ports['share_difficulty']<1 or ports['share_difficulty']>2**24:raise ValueError('Difficulty outside safe range')
            if ports['stratum_port']==ports['dashboard_port']:raise ValueError('Ports must differ')
            runtime.config['node']['binary']=vars['binary'].get().strip()
            runtime.config['node']['data_dir']=vars['data_dir'].get().strip()
            runtime.config['node']['cookie_path']=str(pathlib.Path(vars['data_dir'].get().strip())/'.cookie')
            runtime.config['pool'].update(ports)
            save_config(runtime.config)
            return True
        except Exception as e:
            messagebox.showerror('Invalid configuration',str(e));return False
    def start_node():
        if apply():
            try:runtime.start_node();node_status.set('Node: launched, syncing / awaiting RPC cookie')
            except Exception as e:messagebox.showerror('Node start failed',str(e))
    def start_pool():
        if apply():
            try:runtime.start_pool();pool_status.set('Pool: listening • waiting for node synchronization')
            except Exception as e:messagebox.showerror('Pool start failed',str(e))
    # One-click first-run wizard. Network download and synchronization are never
    # performed on Tk's UI thread; the official Core is verified before install.
    setup_messages=queue.Queue()
    setup_stop=threading.Event()
    setup_busy=[False]
    progress_label=tk.StringVar(value='First run: official VargaMesh Core will be installed automatically.')
    ttk.Label(frame,textvariable=progress_label,style='Hint.TLabel').pack(anchor='w',pady=(7,3))
    progress_bar=ttk.Progressbar(frame,mode='indeterminate',length=450)
    progress_bar.pack(fill='x',pady=(0,5))

    def one_click():
        if setup_busy[0]:return
        if not apply():return
        setup_busy[0]=True
        auto_button.configure(state='disabled')
        setup_stop.clear()
        progress_label.set('Starting verified VMESH-only setup…')
        def work():
            try:
                node=runtime.config['node']
                binary=pathlib.Path(node.get('binary') or '').expanduser()
                if not node.get('binary') or not binary.is_file():
                    if os.name!='nt':
                        raise InstallError('Automatic official Core download is currently Windows-only. On Linux select a VargaMesh Core binary.')
                    rootdir=pathlib.Path(os.getenv('LOCALAPPDATA') or pathlib.Path.home())/'VargaMeshMiniPool'/'core'
                    def on_progress(message,count,total):
                        setup_messages.put(('progress',(message,count,total)))
                    binary=install_windows_core(rootdir,progress=on_progress)
                    node['binary']=str(binary)
                    save_config(runtime.config)
                    setup_messages.put(('binary',str(binary)))
                if setup_stop.is_set():return
                state=runtime.start_node()
                setup_messages.put(('node','Node: '+state+'; synchronizing…'))
                last_error=''
                while not setup_stop.wait(5):
                    if runtime.node_owned and runtime.node_process and runtime.node_process.poll() is not None:
                        raise RuntimeError('Core exited unexpectedly; check the node debug.log file.')
                    try:
                        info=runtime.node_info()
                        blocks=int(info.get('blocks',0))
                        headers=int(info.get('headers',0))
                        percent=100*float(info.get('verificationprogress',0))
                        setup_messages.put(('node',f'Node: {blocks:,}/{headers:,} blocks ({percent:.2f}%)'))
                        # Never issue Stratum jobs until Core considers this mainnet
                        # synchronized, including verification progress and IBD state.
                        if info.get('initialblockdownload',True) or blocks<headers or percent<99.9:
                            continue
                        if setup_stop.is_set():return
                        runtime.start_pool()
                        setup_messages.put(('ready','VMESH SOLO pool ready. Connect a Bitaxe or ASIC.'))
                        return
                    except RPCError as error:
                        message=str(error)[:150]
                        if message!=last_error:
                            setup_messages.put(('node','Node: waiting for Core RPC — '+message))
                            last_error=message
            except Exception as error:
                setup_messages.put(('error',str(error)))
        threading.Thread(target=work,daemon=True,name='VMESH-one-click').start()

    first_run=ttk.Frame(frame)
    first_run.pack(fill='x',pady=(0,10))
    auto_button=ttk.Button(first_run,text='ONE CLICK: Install VMESH Node & Start Pool',command=one_click)
    auto_button.pack(side='left',padx=(0,8))
    ttk.Label(first_run,text='Windows x64 • Core v0.2.0 • 1% VMESH fee',style='Hint.TLabel').pack(side='left')
    buttons=ttk.Frame(frame); buttons.pack(fill='x',pady=(8,10))
    ttk.Button(buttons,text='1. Start VargaMesh Node',command=start_node).pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='2. Start SOLO Pool',command=start_pool).pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='Dashboard ↗',command=lambda:webbrowser.open(f"http://127.0.0.1:{runtime.config['pool']['dashboard_port']}/")).pack(side='left')
    buttons2=ttk.Frame(frame);buttons2.pack(fill='x',pady=(0,12))
    ttk.Button(buttons2,text='Stop Pool',command=lambda:(runtime.stop_pool(),pool_status.set('Pool: stopped'))).pack(side='left',padx=(0,8))
    ttk.Button(buttons2,text='Save configuration',command=apply).pack(side='left',padx=(0,8))
    ttk.Button(buttons2,text='Download official Core ↗',command=lambda:webbrowser.open('https://github.com/ati1993de/vargamesh-core/releases')).pack(side='left')
    log=tk.Text(frame,bg='#111e30',fg='#b9cde6',height=9,relief='flat',font=('Consolas',9),wrap='word')
    log.pack(fill='both',expand=True)
    log.insert('end','No mining yet. Start VargaMesh Core first; wait until it finishes syncing.\n')
    log.configure(state='disabled')
    prior=''
    def update():
        try:
            while True:
                typ,value=setup_messages.get_nowait()
                if typ=='progress':
                    stage,done,total=value
                    progress_label.set(f'{stage}: {done*100//total}%' if total else stage)
                    if total:
                        progress_bar.stop();progress_bar.configure(mode='determinate',maximum=100,value=done*100//total)
                    else:
                        progress_bar.configure(mode='indeterminate');progress_bar.start(14)
                elif typ=='node':
                    node_status.set(value)
                    progress_label.set('Synchronizing VargaMesh mainnet — mining starts automatically when ready.')
                    progress_bar.configure(mode='indeterminate');progress_bar.start(14)
                elif typ=='binary':vars['binary'].set(value)
                elif typ=='ready':
                    progress_bar.stop();progress_bar.configure(mode='determinate',value=100)
                    progress_label.set(value)
                    setup_busy[0]=False;auto_button.configure(state='normal')
                    webbrowser.open(f"http://127.0.0.1:{runtime.config['pool']['dashboard_port']}/")
                elif typ=='error':
                    setup_busy[0]=False;auto_button.configure(state='normal')
                    progress_bar.stop();progress_label.set('Setup failed: '+value)
                    messagebox.showerror('VMESH setup error',value)
        except queue.Empty:pass
        nonlocal prior
        if runtime.pool:
            info=runtime.pool.status()
            pool_status.set(('Pool: ONLINE' if info['node_ready'] else 'Pool: waiting for synced VMESH node')+
                f"  | workers: {info['workers']}  | shares: {info['accepted']}  | blocks: {info['blocks']}")
            entries='\n'.join(time.strftime('%H:%M:%S',time.localtime(e['time']))+'  '+e['message'] for e in reversed(info['events'][:30]))
            if info['node_error']: entries+='\nNode: '+info['node_error']
            if entries!=prior:
                log.configure(state='normal');log.delete('1.0','end');log.insert('end',entries or 'No events');log.see('end');log.configure(state='disabled');prior=entries
        if runtime.node_process and runtime.node_process.poll() is not None:
            node_status.set('Node: exited (check official VargaMesh Core logs)')
        root.after(1500,update)
    def close():
        setup_stop.set()
        runtime.shutdown();root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    update();root.mainloop()


def main():
    parser=argparse.ArgumentParser(description='VMESH-only SHA256d Solo Stratum Pool')
    parser.add_argument('--headless',action='store_true',help='No Tk desktop GUI; dashboard stays available')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    conf=load_config()
    conf['pool'].setdefault('audit_file',str(APP_HOME/'block-finds.jsonl'))
    runtime=Runtime(conf)
    if args.headless: headless(runtime)
    else:gui(runtime)

if __name__=='__main__':main()
