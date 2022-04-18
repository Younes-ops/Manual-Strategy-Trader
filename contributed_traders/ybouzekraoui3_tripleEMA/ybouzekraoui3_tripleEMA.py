# Author: Younes EL BOUZEKRAOUI
# Agent Name: ybouzekraoui3_tripleEMA
#
# The author of this code hereby permits it to be included as a part of the ABIDES distribution, 
# and for it to be released under any open source license the ABIDES authors choose to release ABIDES under.


from agent.TradingAgent import TradingAgent
import pandas as pd
import numpy as np
import os
from contributed_traders.util import get_file

class ybouzekraoui3_tripleEMA(TradingAgent):
    """
    ybouzekraoui3_tripleEMA Trading agent uses 3 moving averages  one short EMA(13), one medium EMA(50), and one long EMA(80) to triger buy and sell signals.
    The moving averages are calculated based on the past mid-price observations.
    It calculates the ratios :
    cross31 = EMA(13)/EMA(80)
    cross32 = EMA(13)/EMA(50)
    cross21 = EMA(50)/EMA(80)

    Then a buy limit order is placed if cross31 <= 0.997 and cross32 <=0.997 and cross21 <=0.999
    And a sell limit order is placer if cross31 >=1.003 and cross32 >=1.003 and cross21 >=1.001

    The agent always trades the maximum possible order size.
    The agent can short the stock however, he cannot short more that 100 stocks.
    The agent cannot buy a stock if it does not have enough cash for it.   
    
    At the end of the day (15 min before the market closes) the agent exits all it's positions (Short position and Long position)
    """

    def __init__(self, id, name, type, symbol, starting_cash,
                 min_size, max_size, wake_up_freq='60s',
                 log_orders=False, random_state=None):

        super().__init__(id, name, type, starting_cash=starting_cash, log_orders=log_orders, random_state=random_state)
        self.symbol = symbol
        self.min_size = min_size  # Minimum order size
        self.max_size = max_size  # Maximum order size
        self.size = max_size
        self.wake_up_freq = wake_up_freq
        self.mid_list, self.avg_win1_list, self.avg_win2_list, self.avg_win3_list = [], [], [], []
        self.sma_list = []
        self.log_orders = log_orders
        self.state = "AWAITING_WAKEUP"
        self.number_of_counting=0

    def kernelStarting(self, startTime):
        super().kernelStarting(startTime)
        # Read in the configuration through util
        with open(get_file('ybouzekraoui3_tripleEMA/ybouzekraoui3_tripleEMA.cfg'), 'r') as f:
            self.window1, self.window2, self.window3 = [int(w) for w in f.readline().split()]
        print(f"{self.window1} {self.window2} {self.window3}")

    def wakeup(self, currentTime):
        """ Agent wakeup is determined by self.wake_up_freq """
        can_trade = super().wakeup(currentTime)
        if not can_trade: return
        self.getCurrentSpread(self.symbol)
        self.state = 'AWAITING_SPREAD'

    def dump_shares(self):
        # get rid of any outstanding shares we have
        if self.symbol in self.holdings and len(self.orders) == 0:
            order_size = self.holdings[self.symbol]
            bid, _, ask, _ = self.getKnownBidAsk(self.symbol)
            if order_size>0:
                if bid:
                    self.placeLimitOrder(self.symbol, quantity=order_size, is_buy_order=False, limit_price=bid)
                    self.number_of_counting +=1
            if order_size<0:
                if ask:
                    #print(order_size)
                    self.placeLimitOrder(self.symbol, quantity=self.max_size, is_buy_order=True, limit_price=ask)
                    self.number_of_counting +=1

    def receiveMessage(self, currentTime, msg):
        """ Momentum agent actions are determined after obtaining the best bid and ask in the LOB """
        super().receiveMessage(currentTime, msg)
        #print(self.number_of_counting)
        if self.state == 'AWAITING_SPREAD' and msg.body['msg'] == 'QUERY_SPREAD':
            dt = (self.mkt_close - currentTime) / np.timedelta64(1, 'm')
            if dt < 15:
                self.dump_shares()
                #print('Fin  i have shares :', self.holdings[self.symbol])
            else:
                bid, _, ask, _ = self.getKnownBidAsk(self.symbol)
                if bid and ask:
                    self.mid_list.append((bid + ask) / 2)
                    if len(self.mid_list) > self.window1: 
                        self.avg_win1_list.append(pd.Series(self.mid_list).ewm(span=self.window1).mean().values[-1].round(2))
                        self.sma_list.append(pd.Series(self.mid_list).rolling(self.window1).mean().values[-1].round(2))
                    if len(self.mid_list) > self.window2: self.avg_win2_list.append(pd.Series(self.mid_list).ewm(span=self.window2).mean().values[-1].round(2))
                    if len(self.mid_list) > self.window3: self.avg_win3_list.append(pd.Series(self.mid_list).ewm(span=self.window3).mean().values[-1].round(2))
                    if len(self.avg_win1_list) > 0 and len(self.avg_win2_list) > 0 and len(self.avg_win3_list) > 0 and len(self.orders) == 0 :

                        
                        #if self.symbol in self.holdings : print('i have shares :', self.holdings[self.symbol])
                        #else: print('i have shares : none')
                    
                       
                        cross31 = self.avg_win3_list[-1]/self.avg_win1_list[-1]
                        cross32 = self.avg_win3_list[-1]/self.avg_win2_list[-1]
                        cross21 = self.avg_win2_list[-1]/self.avg_win1_list[-1]

                        #print(f"{cross31} {cross32} {cross21}  {self.mid_list[-1]} ")

                        if cross31 <= 0.997 and cross32 <=0.997 and cross21 <=0.999:
                            # Check that we have enough cash to place the order
                            if self.holdings['CASH'] >= (self.size * ask):
                                self.placeLimitOrder(self.symbol, quantity=self.size, is_buy_order=True, limit_price=ask)
                                self.number_of_counting +=1
                                #print('-----------buy at :' , ask)                               
                        if cross31 >=1.003 and cross32 >=1.003 and cross21 >=1.001:
                            # Check that we are not shorting more that 100 stocks
                            if super().getHoldings(self.symbol) >= -100:
                                self.placeLimitOrder(self.symbol, quantity=self.size, is_buy_order=False, limit_price= bid)
                                self.number_of_counting +=1
                                #print('-----------sell at :', bid)
            self.setWakeup(currentTime + self.getWakeFrequency())
            self.state = 'AWAITING_WAKEUP'
    def getWakeFrequency(self):
        return pd.Timedelta(self.wake_up_freq)

    def author():              
        return 'ybouzekraoui3'


    def agentname():              
        return 'ybouzekraoui3_tripleEMA'

    def number_of_counting():              
        return self.number_of_counting
