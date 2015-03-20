import agent
import fut_api
#import lts_api
import logging
import misc
import Tkinter as tk
import ttk
import ScrolledText
import sys
import optstrat
import strat_dual_thrust as strat_dt
import datetime
import re

vtype_func_map = {'int':int, 'float':float, 'str': str, 'bool':bool }

def type2str(val, vtype):
    ret = val
    if vtype == 'bool':
        ret = '1' if val else '0'
    elif 'list' in vtype:
        ret = ','.join([str(r) for r in val])
	elif vtype == 'date':
		ret = val.strftime('%Y%m%d')
	elif vtype == 'datetime':
		ret = val.strftime('%Y%m%d %H:%M:%S')
    else:
        ret = str(val)
    return ret

def str2type(val, vtype):
    ret = val
    if vtype == 'bool':
        ret = True if int(float(val))>0 else False
    elif 'list' in vtype:
        key = 'float'    
        if len(vtype) > 4:
            key = vtype[:-4]
        func = vtype_func_map[key]
        ret = [func(s) for s in val.split(',')]
	elif vtype == 'date':
		ret = datetime.datetime.strptime(val,'%y%m%d').date()
	elif vtype == 'datetime':
		ret = datetime.datetime.strptime(val,'%y%m%d %H:%M:%S')
    else:
        func = vtype_func_map[vtype]
        ret = func(float(val))
    return ret

def field2variable(name):
	return '_'.join(re.findall('[A-Z][^A-Z]*', name)).lower()

def variable2field(var):
	return ''.join([s.capitalize() for s in var.split('_')])
	
class StratGui(object):
    def __init__(self, strat, app):
        self.name = strat.name
        self.app = app
        self.underliers = strat.underliers
        self.entries = {}
        self.stringvars = {}
        self.entry_fields = []
        self.status_fields = [] 
        self.field_types = {}
        
    def get_params(self):
        fields = self.entry_fields + self.status_fields
        params = self.app.get_strat_params(self.name, fields)
        for field in fields:
            for idx, underlier in enumerate(self.underliers):
                inst = underlier[0]
                if field in self.entry_fields:
                    ent = self.entries[inst][field]
                    ent.delete(0, tk.END)
                    value = params[field][idx]
                    vtype = self.field_types[field]
                    value = type2str(value, vtype)
                    ent.insert(0, value)
                elif field in self.status_fields:
                    self.stringvars[inst][field].set(str(params[field][idx]))
        return
        
    def set_params(self):
        params = {}
        for field in self.entry_fields:
            params[field] = []
            for underlier in self.underliers:
                inst = underlier[0]
                ent = self.entries[inst][field]
                value = ent.get()
                vtype = self.field_types[field]
                value = str2type(value, vtype)
                params[field].append(value)
        self.app.set_strat_params(self.name, params)
        return
        
    def frame(self, root):
        self.lblframe = tk.LabelFrame(root)
        self.lblframe.grid_columnconfigure(1, weight=1)
        fields = ['inst'] + self.entry_fields + self.status_fields
        for idx, field in enumerate(fields):
            lbl = tk.Label(self.lblframe, text = field, anchor='w')
            lbl.grid(row=0, column=idx, sticky="ew")
        row_id = 1
        entries = {}
        stringvars = {}
        for underlier in self.underliers:
            inst = str(underlier[0])
            inst_lbl = tk.Label(self.lblframe, text=inst, anchor="w")
            inst_lbl.grid(row=row_id, column=0, sticky="ew")
            col_id = 1
            entries[inst] = {}
            for idx, field in enumerate(self.entry_fields):
                ent = tk.Entry(self.lblframe)
                ent.grid(row=row_id, column=col_id+idx, sticky="ew")
                ent.insert(0, "0")
                entries[inst][field] = ent
            col_id += len(self.entry_fields)
            stringvars[inst] = {}
            for idx, field in enumerate(self.status_fields):
                v = tk.StringVar()
                lab = tk.Label(self.lblframe, textvariable = v, anchor='w')
                lab.grid(row=row_id, column=col_id+idx, sticky="ew")
                v.set('0')
                stringvars[inst][field] = v       
            row_id +=1
        self.entries = entries
        self.stringvars = stringvars
        
        set_btn = tk.Button(self.lblframe, text='Set', command=self.set_params)
        set_btn.grid(row=row_id, column=1, sticky="ew")
        refresh_btn = tk.Button(self.lblframe, text='Refresh', command=self.get_params)
        refresh_btn.grid(row=row_id, column=2, sticky="ew")
        recalc_btn = tk.Button(self.lblframe, text='Recalc', command=self.recalc)
        recalc_btn.grid(row=row_id, column=3, sticky="ew")
        self.lblframe.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
    def recalc(self):
        self.app.run_strat_func(self.name, 'initialize')

class DTStratGui(StratGui):
    def __init__(self, strat, app):
        StratGui.__init__(self, strat, app)
        self.entry_fields = ['trade_unit', 'lookbacks', 'ratios', 'close_tday']
        self.status_fields = ['tday_open', 'cur_rng'] 
        self.field_types = {'trade_unit':'int', 
                            'lookbacks':'int', 
                            'ratios': 'floatlist', 
                            'close_tday': 'bool',
                            'tday_open': 'float', 
                            'cur_rng':'float' }
                        
class RBStratGui(StratGui):
    def __init__(self, strat, app):
        StratGui.__init__(self, strat, app)
        self.entry_fields = ['trade_unit', 'min_rng', 'ratios', 'close_tday', 'start_min_id']
        self.status_fields = ['sbreak', 'bsetup', 'benter', 'senter', 'ssetup', 'bbreak'] 
        self.field_types = {'trade_unit':'int', 
                            'min_rng':'float', 
                            'ratios': 'floatlist', 
                            'close_tday': 'bool',
                            'start_min_id': 'int',
                            'sbreak': 'float', 
                            'bbreak':'float',
                            'bsetup':'float', 
                            'benter':'float', 
                            'senter':'float', 
                            'ssetup':'float' }        
    
class OptStratGui(object):
    def __init__(self, strat, app):
        self.name = strat.name
        self.app = app
        self.underliers = strat.underliers
		self.option_insts = strat.option_insts.keys()
		self.option_expiries = strat.expiries
        self.entries = {}
        self.stringvars = {}
        self.entry_fields = []
        self.status_fields = [] 
        self.field_types = {}

	def get_params(self, fields):
		pass
		
	def set_params(self, params):
		pass
	
	def frame(self, root):
		self.lblframe = tk.LabelFrame(root)
        self.lblframe.grid_columnconfigure(1, weight=1)
		pass
    
class Gui(tk.Tk):
    def __init__(self, app = None):
        tk.Tk.__init__(self)       
        self.title(app.name)
        self.app = app
        if app!=None:
            self.app.master = self
        #self.scroll_text = ScrolledText.ScrolledText(self, state='disabled')
        #self.scroll_text.configure(font='TkFixedFont')
        # Create textLogger
        #self.text_handler = TextHandler(self.scroll_text)
        #self.scroll_text.pack()
        self.settings_win = None
        self.setup_app = None
        self.status_win = None
        self.status_app = None
        self.setup_ents = {}
        self.status_ents = {}
        self.strat_frame = {}
        self.strat_gui = {}
        for strat in self.app.agent.strategies:
            if strat.__class__.__name__ == 'DTTrader':
                self.strat_gui[strat.name] = DTStratGui(strat, app)
            elif strat.__class__.__name__ == 'RBreakerTrader':
                self.strat_gui[strat.name] = RBStratGui(strat, app)
            elif 'Opt' in strat.__class__.__name__:
                self.strat_gui[strat.name] = OptStratGui(strat, app)
        menu = tk.Menu(self)
        #menu.add_command(label="Settings", command=self.config_settings)
        menu.add_command(label="Status", command=self.onStatus)
        menu.add_command(label="Reset", command=self.onReset)
        menu.add_command(label="Exit", command=self.onExit)
        self.config(menu=menu)
		self.notebook = ttk.Notebook(self)
        #stratmenu = tk.Menu(menu)
        #menu.add_cascade(label="Strategies", menu=stratmenu)
        for strat in self.app.agent.strategies:
            #stratmenu.add_command(label = strat.name, command=(lambda name = strat.name: self.onStratNewWin(name)))
			name = strat.name
			self.strat_frame[name] = ttk.Frame(self)
			self.strat_gui[name].frame(self.strat_frame[name])
			self.notebook.add(self.strat_frame[name], text = name)
		self.settings_win = ttk.Frame(self.notebook)
		self.config_settings()
		self.notebook.pack()
        self.setup_fields = ['MarketOrderTickMultiple', 'CancelProtectPeriod', 'MarginCap']
        self.status_fields = ['Positions', 'Orders', 'Trades', 'Insts', 'ScurDay', 'EodFlag', 'Initialized', 'ProcLock', \
                              'CurrCapital', 'PrevCapital', 'LockedMargin', 'UsedMargin', 'Available', 'PnlTotal']

    # def onStratNewWin(self, name):
        # strat_gui = self.strat_gui[name]
        # top_level = tk.Toplevel(self)
        # top_level.title('strategy: %s' % name)
        # strat_gui.start(top_level)
        # return 
        
    def config_settings(self):
        self.setup_ents = self.make_setup_form(self.settings_win, self.setup_fields)
        #self.settings_win.bind('<Return>', self.set_agent_params)
        self.setup_setbtn = tk.Button(self.settings_win, text='Set', command=self.set_agent_params)
        self.setup_setbtn.pack(side=tk.LEFT, padx=5, pady=5)
        self.setup_loadbtn = tk.Button(self.settings_win, text='Load', command=self.get_agent_params)
        self.setup_loadbtn.pack(side=tk.LEFT, padx=5, pady=5)
        self.get_agent_params()
    
    def set_agent_params(self):
        params = {}
        for field in self.setup_fields:
            ent = self.setup_ents[field]
            value = ent.get()
            params[field] = value        
        self.app.set_agent_params(params)
        pass
    
    def get_agent_params(self):
        params = self.app.get_agent_params(self.setup_fields)
        for field in self.setup_fields:
            ent = self.setup_ents[field]
            ent.delete(0, tk.END)
            ent.insert(0, str(params[field]))
        return

#    def fetch(self, entries):
#        for entry in entries:
#            field = entry[0]
#            text  = entry[1].get()
#            print('%s: "%s"' % (field, text)) 
          
    def make_setup_form(self, root, fields):
        entries = {}
        for field in fields:
            row = tk.Frame(root)
            lab = tk.Label(row, width=22, text=field+": ", anchor='w')
            ent = tk.Entry(row)
            ent.insert(0,"0")
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries[field] = ent
        return entries
        
    def refresh_agent_status(self):
        pass
    
    def make_status_form(self):
        pass
        
    def onStatus(self):
        self.status_win = tk.Toplevel(self)
        self.status_ents = self.make_status_form(self.status_win)        
        
    def onReset(self):
        self.app.reset_agent()

    def onExit(self):
        self.app.exit_agent()
        self.destroy()
        return
        
        
class MainApp(object):
    def __init__(self, name, trader_cfg, user_cfg, strat_cfg, tday, master = None):
        self.trader_cfg = trader_cfg
        self.user_cfg = user_cfg
        self.strat_cfg = strat_cfg
        self.scur_day = tday
        self.name = name
        self.agent = None
        self.master = master
        self.reset_agent()
		self.field_types = {'ProcLock': 'bool',
							'ScurDay' : 'date',
							'EodFlag' : 'bool',
							'MarketOrderTickMultiple': 'int', 
							'CancelProtectPeriod': 'int', 
							'MarginCap': 'float'}
							
    def reset_agent(self):       
        if self.agent != None:
            self.scur_day = self.agent.scur_day
        all_insts= []
        for strat in self.strat_cfg['strategies']:
            all_insts = list(set(all_insts).union(set(strat.instIDs)))
        self.agent = fut_api.create_agent(self.name, self.user_cfg, self.trader_cfg, all_insts, self.strat_cfg, self.scur_day)
        #self.agent.logger.addHandler(self.text_handler)
        #fut_api.make_user(self.agent, self.user_cfg)
        self.agent.resume()
        return
    
    def get_agent_params(self, fields):
        res = {}
        for field in fields:
            if field == 'Positions':
                positions = []
                for inst in self.agent.positions:
                    pos = self.agent.positions[inst]
                    positions.append([inst, pos.curr_pos.long, pos.curr_pos.short, self.locked_pos.long, self.locked_pos.short])
                res[field] = positions
            elif field == 'Orders':
                order_list = []
                for o in self.agent.ref2order.values():
                    inst = o.position.instrument.name
                    order_list.append([o.order_ref, o.sys_id, inst, o.diretion, o.volume, o.filled_volume,  o.limit_price, o.status])
                res[field] = order_list
            elif field == 'Trades':
                trade_list = []
                for etrade in self.agent.etrades:
                    insts = ' '.join(etrade.instIDs)
                    volumes = ' '.join([str(i) for i in etrade.volumes])
                    filled_vol = ' '.join([str(i) for i in etrade.filled_vol])
                    filled_price = ' '.join([str(i) for i in etrade.filled_price])
                    trade_list.append([etrade.id, insts, volumes, filled_vol, filled_price, etrade.limit_price, etrade.valid_time,
                                  etrade.strategy, etrade.book, etrade.status])
                res[field] = trade_list
            elif field == 'Insts':
                inst_list = []
                for inst in self.agent.instruments:
                    inst_obj = self.agent.instruments[inst]
                    inst_list.append([inst, inst_obj.price, inst_obj.bid_price1, inst_obj.bid_vol1, 
                                      inst_obj.ask_price1, inst_obj.ask_vol1, inst_obj.prev_close, 
                                      inst_obj.marginrate, inst_obj.last_update, inst_obj.last_traded])
                res[field] = inst_list
			else:
				var = field2variable(field)
				value = getattr(self.agent, var)
				res[field] = type2str(value, value.__class__.__name__)
        return res

    def set_agent_params(self, params):
        for field in params:
			var = field2variable(field)
			value = params[field]
			if field in self.field_types:
				vtype = self.field_types[field]
				value = str2type(value, vtype)
			setattr(self.agent, var, value)
        return
    
    def get_strat_params(self, strat_name, fields):
        params = {}
        for strat in self.agent.strategies:
            if strat.name == strat_name:
                for field in fields:
                    params[field] = getattr(strat, field)
                break 
        return params
    
    def set_strat_params(self, strat_name, params):
        for strat in self.agent.strategies:
            if strat.name == strat_name:
                for field in params:
                    setattr(strat, field, params[field])
                break 
        return
    
    def run_strat_func(self, strat_name, func_name):
        for strat in self.agent.strategies:
            if strat.name == strat_name:
                getattr(strat, func_name)()
                break 
        return 
        
    def exit_agent(self):
        if self.agent != None:
            self.agent.mdapis = []
            self.agent.trader = None
        return

def main(tday, name='option_test'):
    logging.basicConfig(filename="ctp_" + name + ".log",level=logging.DEBUG,format='%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(levelname)s %(message)s')
    trader_cfg = misc.TEST_TRADER
    user_cfg = misc.TEST_USER
    opt_strat = optstrat.IndexFutOptStrat(name, 
                                    ['IF1503', 'IF1506'], 
                                    [datetime.datetime(2015, 3, 20, 15, 0, 0), datetime.datetime(2015,6,19,15,0,0)],
                                    [[3400, 3450, 3500, 3550, 3600, 3650]]*2)
    insts_dt = ['IF1503']
    units_dt = [1]*len(insts_dt)
    under_dt = [[inst] for inst in insts_dt]
    vols_dt = [[1]]*len(insts_dt)
    lookbacks_dt = [0]*len(insts_dt)
    
    insts_daily = ['IF1503']
    under_daily = [[inst] for inst in insts_daily]
    vols_daily = [[1]]*len(insts_daily)
    units_daily = [1]*len(insts_daily)
    lookbacks_daily = [0]*len(insts_daily)

    dt_strat = strat_dt.DTTrader('DT_test', under_dt, vols_dt, trade_unit = units_dt, lookbacks = lookbacks_dt, agent = None, daily_close = False, email_notify = [])
    dt_daily = strat_dt.DTTrader('DT_Daily', under_daily, vols_daily, trade_unit = units_daily, lookbacks = lookbacks_daily, agent = None, daily_close = True, email_notify = ['harvey_wwu@hotmail.com'])
    
    strategies = [dt_strat, dt_daily, opt_strat]
    strat_cfg = {'strategies': strategies, \
                 'folder': 'C:\\dev\\src\\ktlib\\pythonctp\\pyctp\\', \
                 'daily_data_days':3, \
                 'min_data_days':1 }
    
    myApp = MainApp(name, trader_cfg, user_cfg, strat_cfg, tday, master = None)
    myGui = Gui(myApp)
    myGui.mainloop()
    
if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        app_name = 'option_test'
    else:
        app_name = args[1]       
    if len(args) < 1:
        tday = datetime.date.today()
    else:
        tday = datetime.datetime.strptime(args[0], '%Y%m%d').date()

    main(tday, app_name)    
    
