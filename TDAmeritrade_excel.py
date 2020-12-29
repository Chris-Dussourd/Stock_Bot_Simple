import time,datetime
import xlsxwriter

def save_results(tickers_list,bid_prices,bid_sizes,ask_prices,ask_sizes,bidask_times):
    """
    Stores bid and ask data for stocks into an excel spreadsheet. Used for plotting.
    tickers_list - list of all the tickers that we got data for
    bid_prices - the bid prices for each ticker over time
    bid_sizes - the number of buy orders placed at the bid price over time
    ask_prices - the ask prices for each ticker over time
    ask_sizes - the number of sell orders placed at the ask price over time
    bidask_times - the times array at which each data point was obtained
    """

    #Load workbook to add information to
    workbook = xlsxwriter.Workbook('Bid_Ask_Data.xlsx')
    worksheet = workbook.add_worksheet('5-12-2020')

    #Add 5 columns for each ticker (bid price, bid size, ask price, ask size, bid/ask times)
    for i,ticker in enumerate(tickers_list):
        worksheet.write(0,4*i+1,ticker)

        #Each row is a new time point
        for row in range(len(bidask_times)):
            if i == 0:
                #Only add bid ask times once (all the times are the same for each ticker)
                worksheet.write(row+1,i,bidask_times[row])
            #Write data to excel file
            worksheet.write(row+1,1+4*i,bid_prices[ticker][row])
            worksheet.write(row+1,2+4*i,bid_sizes[ticker][row])
            worksheet.write(row+1,3+4*i,ask_prices[ticker][row])
            worksheet.write(row+1,4+4*i,ask_sizes[ticker][row])

    #Close excel workbook
    workbook.close()