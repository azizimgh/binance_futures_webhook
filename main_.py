
from datetime import datetime
import json
from datetime import datetime
from flask import Flask, request
from binance_futures_webhook.binance_handler import binance_handler as handle_trades



app = Flask(__name__)


def write_log_txt(line):
    with open('logs.txt','a') as  fl:
        print(line)
        fl.write(str(datetime.now())+':'+line+'\n')

def write_tardes(line):
    with open('trades_recieved.txt','a') as  fl:
        tm = str(datetime.now().year)+str(datetime.now().month) + str(datetime.now().day)+str(datetime.now().hour)+str(datetime.now().minute)+str(datetime.now().second)
        fl.write(line+':'+tm+'\n')

def write_orders(line_id):
    with open('orders.txt','a') as  fl:
        print(line_id)
        fl.write('\n'+line_id+":"+str(datetime.now())+'\n')
        
def write_longs(line_id):
    with open('longs.txt','a') as  fl:
        print(line_id)
        fl.write('\n'+line_id+":"+str(datetime.now())+'\n')

def write_shorts(line_id):
    with open('shorts.txt','a') as  fl:
        print(line_id)
        fl.write('\n'+line_id+":"+str(datetime.now())+'\n')



@app.route("/")
def hello_world():
    return "<h1>The app is up and runninng</h1>"


        


@app.route("/binance", methods=["POST"])
def binance():
    global balance,id_short,id_long
    data = json.loads(request.data)

    try:

        print(data)
        key = data['key']
        sec = data['sec']
        side = data['side']
        symbol = data['symbol']
        quantity = float(data['quantity'])
        price = float(data['price'])
        #security = float(data['security'])
        if 'tp' in data['comment'].lower():
            return {
            "code": "it is a tp "
        }
        comment  = data['comment'].lower().strip('buy').strip('sell').strip().split(',')

        lm = float(comment[0]) 
        sl = float(comment[2])       
        tp = float(comment[1])


        print('lm price', lm)
        """
        0.1% - 0.99%	50
        1.0% - 1.49%	48
        1.5% - 1.99%	40
        2.0% - 2.49%	33
        2.5% - 2.99%	28
        3.0% - 3.49%	25
        3.5% - 3.99%	22
        """
        change = abs((price-sl)/sl*100)
        leverage = 10
        if change <1:
            leverage = 25
        elif change <1.5:
            leverage = 25
        elif change <2:
            leverage = 25
        elif change <2.5:
            leverage = 20
        elif change <3:
            leverage = 15
        elif change <3.5:
            leverage = 15
        elif change <4:
            leverage = 15
        
        if side.lower() in ['buy', "long"]:
            tst = handle_trades(key,sec)
            balance = tst.get_portfolio()            
            quantity = balance/price*leverage*quantity/100
            print(str(price).split('.')[1])
            precision = len(str(price).split('.')[1])
            tp = round(tp,precision)
            sl = round(sl,precision)
            lm = round(lm,precision)
            print("Balance: ",balance)      
            print(f'Trying to place trade for {symbol} qt {quantity} lm {lm}  tp {tp}  sl {sl} lv {leverage} ')  
            print("Balance: ",balance)      
            no_position = tst.get_and_close_open_position(symbol,side_new="long")  
            tst.change_leverage(ticker=symbol,leverage=leverage)
            if no_position and price>sl:
                tst.cancel_order(symbol)   
                print('Placing long stop limit order: ') 
                place_tp_sl = False
                
                res =tst.place_stop_limit_long_order(ticker=symbol, quantity=quantity,price=lm)

                if not res[0] :
                    print('     Not placed, trying market order')
                    res = tst.place_market_long_order(ticker=symbol, quantity=quantity,price=0)
                    if  res[0] :
                        print('     Market placed')
                        place_tp_sl = True
                else:
                    write_orders(symbol +":"+"buy"+":"+str(sl)+":"+ str(res[0])) 
                    write_longs(symbol +":"+"buy"+":"+str(sl)+":"+ str(res[0]))
                    place_tp_sl = True
                if  place_tp_sl:
                    tst.place_tp_long_order(ticker=symbol, quantity=quantity,price=tp)
                    tst.place_sl_long_order(ticker=symbol, quantity=quantity,price=sl)

                
        elif side.lower() in ['sell', "short"]:
            tst = handle_trades(key,sec)            
            balance = tst.get_portfolio()
            quantity = balance/price*leverage*quantity/100
            precision = len(str(price).split('.')[1])
            tp = round(tp,precision)
            sl = round(sl,precision)
            lm = round(lm,precision)
            print("Balance: ",balance)    
            print(f'Trying to place trade for {symbol} qt {quantity} lm {lm}  tp {tp}  sl {sl} lv {leverage} ')  
            no_position = tst.get_and_close_open_position(symbol,side_new="short")  
            place_tp_sl = False
            tst.change_leverage(ticker=symbol,leverage=leverage)
            if no_position and price<sl:
                tst.cancel_order(symbol)   
                print('Placing short stop limit order: ') 
                res = tst.place_stop_limit_short_order(ticker=symbol, quantity=quantity,price=lm)
                if not res[0] :
                    print('     Not placed, trying market order')
                    res = tst.place_market_short_order(ticker=symbol, quantity=quantity,price=0)
                    if  res[0] :
                        place_tp_sl = True
                else:                    
                    write_orders(symbol +":"+"sell"+":"+str(sl)+":"+ str(res[0]))
                    write_shorts(symbol +":"+"sell"+":"+str(sl)+":"+ str(res[0]))
                    place_tp_sl = True
                if  place_tp_sl:
                    tst.place_tp_short_order(ticker=symbol, quantity=quantity,price=tp)
                    tst.place_sl_short_order(ticker=symbol, quantity=quantity,price=sl)
        return {
            "code": "ok: "
        }

    except Exception as e:
        return {
            "code" : "Error: " +str(e)
            }



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)
