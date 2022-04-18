# Author: Younes EL BOUZEKRAOUI
# Agent Name: ybouzekraoui3_tripleEMA
#
# The author of this code hereby permits it to be included as a part of the ABIDES distribution, 
# and for it to be released under any open source license the ABIDES authors choose to release ABIDES under.


This agent is inspired from the the simpleAgent given in this project.
However It is based on the Triple Moving Average Trading system.
It uses 3 moving averages (EMA) one short, one medium, and one long to triger buy and sell signals.
The moving averages are calculated based on the past mid-price observations.

Long Moving Average : EMA(80)
Medium Moving Average : EMA(50)
Short Moving Average : EMA(13)


It calculates the ratios :
cross31 = EMA(13)/EMA(80)
cross32 = EMA(13)/EMA(50)
cross21 = EMA(50)/EMA(80)

Then a buy limit order is placed if cross31 <= 0.997 and cross32 <=0.997 and cross21 <=0.999
And a sell limit order is placer if cross31 >=1.003 and cross32 >=1.003 and cross21 >=1.001

The agent always trades the maximum possible order size.
The agent can short the stock however, he cannot short more that 100 stocks.
The agent cannot buy a stock if it does not have enough cash for it.
    
At the end of the day (15 min before the market closes) the agent exits all it's positions (Both Short and Long positions).
