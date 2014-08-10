import datetime
import requests
import os
import json

BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
LAST_DIR = os.path.join(BASE_DATA_DIR, "last")
BID_DIR = os.path.join(BASE_DATA_DIR, "bid")
ASK_DIR = os.path.join(BASE_DATA_DIR, "ask")
SYMBOLS_FILE = os.path.join(BASE_DIR, "symbols.txt")
META_FILE = os.path.join(BASE_DIR, "meta.json")

TICK_BASE_URL = "http://hopey.netfonds.no/tradedump.php"
QUOTE_BASE_URL = "http://hopey.netfonds.no/posdump.php"

EXCHANGE_CODES = ['O', 'N', 'A']

start_date = (datetime.datetime.now() - datetime.timedelta(20)).date()
latest_date = (datetime.datetime.now()- datetime.timedelta(1)).date()

def make_dirs():
    if not os.path.isdir(os.path.join(BASE_DATA_DIR)):
        os.mkdir(BASE_DATA_DIR)
    if not os.path.isdir(LAST_DIR):
        os.mkdir(LAST_DIR)
    if not os.path.isdir(ASK_DIR):
        os.mkdir(ASK_DIR)
    if not os.path.isdir(BID_DIR):
        os.mkdir(BID_DIR)
    if not os.path.isfile(META_FILE):
        with open(META_FILE, 'w') as f:
            f.write("{}")


def get_exchange_code(sym):
    def prev_weekday():
        adate = datetime.datetime.now().date() - timedelta(days=1)
        while adate.weekday() > 4: # Mon-Fri are 0-4
            adate -= timedelta(days=1)
        return adate

    for c in EXCHANGE_CODES:
        request_args = {
            'date': prev_weekday().strftime("%Y%m%d"),
            'paper': sym + "." + c,
            'csv_format': 'txt'
        }
        r = requests.get(TICK_BASE_URL, params=request_args)
        if r.ok:
            if r.text[:15] != u'<!DOCTYPE HTML>' and len(r.text.split('\n')) > 2:
                return c
    return "X"
    

def capture_day(sym, meta, _datestr):
    def send_tick_request():
        r = requests.get(TICK_BASE_URL, params=GET_ARGS)
        with open(os.path.join(LAST_DIR, ".".join([sym, "Last", "txt"])), 'a') as flast:
            for line in r.text.split('\n')[1:-1]:
                data = line.split("\t")
                if len(data) >= 3:
                    flast.write(";".join([data[0].replace("T", " "), data[1], data[2]]) + "\n")

    def send_quote_request():
        r = requests.get(QUOTE_BASE_URL, params=GET_ARGS)
        fask = open(os.path.join(ASK_DIR, ".".join([sym, "Ask", "txt"])), 'a')
        fbid = open(os.path.join(BID_DIR, ".".join([sym, "Bid", "txt"])), 'a')
        for line in r.text.split('\n')[1:-1]:
            data = line.split("\t")
            if len(data) >= 6:
                fask.write(";".join([data[0].replace("T", " "), data[1], data[2]]) + "\n")
                fbid.write(";".join([data[0].replace("T", " "), data[4], data[5]]) + "\n")
        fask.close()
        fbid.close()

    GET_ARGS = {}
    GET_ARGS['date'] = _datestr
    GET_ARGS['paper'] = sym + "." + meta[sym]['code']
    GET_ARGS['csv_format'] = "txt"

    send_tick_request()
    send_quote_request()

    meta[sym]['date'] = _datestr
    
    
def capture_sym(sym, meta):
    global start_date, latest_date
    if sym in meta:
        sym_start_date = datetime.datetime.strptime(meta[sym].get('date', '20000101'), "%Y%m%d").date() + datetime.timedelta(1)
        if sym_start_date > latest_date:
            return
        if sym_start_date < start_date:
            sym_start_date = start_date
    else:
        meta[sym] = {}
        meta[sym]['code'] = get_exchange_code(sym)
        sym_start_date = start_date
    days = (latest_date - sym_start_date).days
    if not 'code' in meta[sym]:
        meta[sym]['code'] = get_exchange_code(sym)
    if meta[sym]['code'] == "X":
        return
    for n in xrange(0, days):
        _datestr = (sym_start_date + datetime.timedelta(n)).strftime("%Y%m%d")
        capture_day(sym, meta, _datestr)
        print sym + "." + meta[sym]['code'] + " - " + _datestr


def main():
    make_dirs()
    with open(SYMBOLS_FILE) as f:
        syms = f.read().split('\n')
    with open(META_FILE) as f:
        meta = json.loads(f.read())
    for sym in syms:
        capture_sym(sym, meta)
        with open(META_FILE, 'w') as f:
            f.write(json.dumps(meta))



if __name__ == "__main__":
    main()
