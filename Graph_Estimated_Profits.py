
import pickle
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt

profit_ticker_percent = pickle.load(open("PofitbyPercent_SellNewBuy_April3_May15_3_SGBX.p","rb"))
sell_percent = pickle.load(open("SellPercent_SGBX.p","rb"))
new_buy_percent = pickle.load(open("NewBuyPercent_SGBX_Sell.p","rb"))

for ticker in profit_ticker_percent:
    fig = plt.figure()
    ax = plt.axes(projection='3d')

    #Plot the data
    ax.plot3D(sell_percent,new_buy_percent,profit_ticker_percent[ticker],'gray')

    print(ticker)
    plt.show()
    
    
