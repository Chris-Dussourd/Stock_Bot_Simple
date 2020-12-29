import pyodbc,datetime


def store_results(transactions):
    """
    Stores the results of the Bot in tables in SQL database
    transactions - contains all the data
        transactions['Buy History'] - list of tuples of (orderID,price, amount, placed_time, filled_time) of past filled limit buy orders
        transactions['Sell History'] - list tuples of (orderID, price, amount, placed_time, filled_time,parentOrderID) of past filled limit sell orders
    """

    server='LAPTOP-N3JOPONO'
    database='TD_Ameritrade'
    data_connection=pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};\
                                    SERVER=' + server + ';\
                                    DATABASE=' + database + ';\
                                    Trusted_Connection=yes;')

    data_cursor=data_connection.cursor()

    symbol = transactions['Stock Symbol']
    #Add buy history to SQL table
    for (orderID,price,quantity,placed_time,filled_time) in transactions['Buy History']:

        #Insert query to insert new data into Buy_Orders table
        insert_query_buy = '''INSERT INTO Buy_Orders(Buy_Order_ID,Stock_Ticker,Price,Quantity,Time_Placed,Time_Filled)
                              VALUES(?,?,?,?,?,?);'''

        #Information on buy transactions
        values_buy=(orderID,symbol,price,quantity,placed_time,filled_time)
        data_cursor.execute(insert_query_buy,values_buy)

    #Add sell history to SQL Table
    for (orderID,price,quantity,placed_time,filled_time,parentID) in transactions['Sell History']:

        #Insert query to insert new data into Sell_Orders table
        insert_query_sell = '''INSERT INTO Sell_Orders(Sell_Order_ID,Stock_Ticker,Price,Quantity,Time_Placed,Time_Filled,Buy_Order_ID_link)
                               VALUES(?,?,?,?,?,?,?);'''

        #Information on sell transactions
        values_sell=(orderID,symbol,price,quantity,placed_time,filled_time,parentID)
        data_cursor.execute(insert_query_sell,values_sell)

    #Add current open sell orders to SQL Table
    for (orderID,price,parentID) in transactions['Limit Sells']:

        #Insert query to insert new data into Open_Sell_Orders table
        insert_query_sell_open = '''INSERT INTO Open_Sell_Orders(Sell_Order_ID,Stock_Ticker,Price,Date,Buy_Order_ID_link)
                                    VALUES(?,?,?,?,?);'''

        #Information on sell transactions
        values_sell_open=(orderID,symbol,price,datetime.datetime.now().date(),parentID)
        data_cursor.execute(insert_query_sell_open,values_sell_open)


    data_connection.commit()
    data_cursor.close()
    data_connection.close()


def retrieve_open_orders(transactions):
    """
    Get the open orders in the table Open Sell Orders

    Returns list of tuples of (orderID,price,parentID,date) of orders that were not filled the previous day
    """
    transactions['Old Open Orders'] = []

    server='LAPTOP-N3JOPONO'
    database='TD_Ameritrade'
    data_connection=pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};\
                                    SERVER=' + server + ';\
                                    DATABASE=' + database + ';\
                                    Trusted_Connection=yes;')

    data_cursor=data_connection.cursor()

    data_cursor.execute('SELECT Sell_Order_ID,Price,Buy_Order_ID_link FROM Open_Sell_Orders;')

    for row in data_cursor:
        transactions['Old Open Orders'].append((row[0].strip(),float(round(row[1],2)),row[2].strip()))



def update_open_orders(transactions):
    """
    Deletes values from the open orders table and adds in the new open orders
    transactions['Limit Sells'] - contains a list of open limit sell orders
    """

    server='LAPTOP-N3JOPONO'
    database='TD_Ameritrade'
    data_connection=pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};\
                                    SERVER=' + server + ';\
                                    DATABASE=' + database + ';\
                                    Trusted_Connection=yes;')

    data_cursor=data_connection.cursor()

    symbol = transactions['Stock Symbol']

    #Delete old open order data
    delete_query = """DELETE FROM Price_Data WHERE Stock_Ticker={}""".format(symbol)
    data_cursor.execute(delete_query)
    data_connection.commit()


    #Add current open sell orders to SQL Table
    for (orderID,price,parentID) in transactions['Limit Sells']:

        #Insert query to insert new data into Open_Sell_Orders table
        insert_query_sell_open = '''INSERT INTO Open_Sell_Orders(Sell_Order_ID,Stock_Ticker,Price,Date,Buy_Order_ID_link)
                                    VALUES(?,?,?,?,?);'''

        #Information on sell transactions
        values_sell_open=(orderID,symbol,price,datetime.datetime.now().date(),parentID)
        data_cursor.execute(insert_query_sell_open,values_sell_open)


    data_connection.commit()
    data_cursor.close()
    data_connection.close()
