'''
A readme is included in the repo that details language/design choices, as well 
as potential improvements.  
'''

import gzip as gz
import struct as st
from collections import defaultdict
from datetime import datetime, timedelta

inputFile = '01302019.NASDAQ_ITCH50.gz'
inputFile = gz.open(inputFile, 'rb')
bytePosition = 0
systemEventCodes = set(['O', 'S', 'Q', 'M', 'E'])

# tradesdict is a dictionary that maps stock names to the sum of all (volume * price) for the day's trades and volume total
tradesdict = {}
messageTypeDict = {b'S': 11, b'R': 38, b'H': 24, b'Y': 19, b'L': 25, b'V': 34, b'W': 11, b'k': 27, b'J': 34, b'h': 20, b'A': 35, b'F': 39, b'E': 30, b'C': 35, b'X': 22, b'D': 18, b'P': 43, b'Q': 39, b'B': 18, b'I': 49, b'O': 44, b'U': 34}

"""
Waits for the byte location of the 
market open, marked by  'Q' signal 
at event code
"""
def wait_for_market_open(inputFile):
    eventCode = ''
    while eventCode != 'Q':
        eventMessage = ''
        while eventMessage != b'S':
            eventMessage = inputFile.read(1)
            try:
                eventMessage.decode()
            except UnicodeDecodeError:
                pass
        followingMessage = inputFile.read(11)
        messagelist = []
        for byte in followingMessage:
            try:
                byte = byte.decode()
                messagelist.append(byte)
            except AttributeError:
                messagelist.append(byte)
        eventCode = chr(messagelist[-1])
    return None


"""
Parses all messages, checking to see if they are relevant to our VWAP
and skipping otherwise.
"""
def parse_messages(inputFile, tradesdict, hourly_vwap_dict):
    time = 0
    eod = False
    firstByte = inputFile.read(1)
    while firstByte and eod == False:
        while firstByte not in messageTypeDict:
            firstByte = inputFile.read(1)
            if not firstByte:  # Check for end of file
                break

        messagelen = messageTypeDict[firstByte]
        message = inputFile.read(messagelen)
        if firstByte == b'P':  # TRADE HAS OCCURRED
            tradesdict, hourly_vwap_dict = parse_for_vwap(message, messagelen, tradesdict, hourly_vwap_dict)
        firstByte = inputFile.read(1)
        if firstByte == b'S':
            followingMessage = inputFile.read(11)
            messagelist = []
            for byte in followingMessage:
                try:
                    byte = byte.decode()
                    messagelist.append(byte)
                except AttributeError:
                    messagelist.append(byte)
            eventCode = chr(messagelist[-1])
            if eventCode == 'M':
                eod = True
    return tradesdict, hourly_vwap_dict

"""
If we find a message that impacts our vwap, we move here
to verify that it is a buy/sell order.  Then,
we can update our dict if needed or simply
update our vwap calculation values
"""
def parse_for_vwap(message, messagelen, tradesdict, hourly_vwap_dict):
    if chr(message[18]) == 'B' or chr(message[18]) == 'S':  # BUY or SELL HAS OCCURRED
        shares = st.unpack('<I', message[19:23])[0]  # Shares is an unsigned integer
        #print(shares)
        stock = message[23:31].decode('utf-8').rstrip()  # Stock symbol, padded with spaces
        price_int = st.unpack('<I', message[32:36])[0]  # Price is an unsigned integer
        price_precision = 4  # Assuming Price (4) format
        price = price_int / (10 ** price_precision)  # Convert to decimal with 4 decimal places

        #print(price)
        timestamp_bytes = message[4:10] + b'\x00\x00'
        timestamp = st.unpack('<Q', timestamp_bytes)[0] / 1000000000
        trade_time = datetime.fromtimestamp(timestamp)

        if stock in tradesdict:
            tradesdict[stock][0] += shares * price
            tradesdict[stock][1] += shares
        else:
            tradesdict[stock] = [shares * price, shares]

        # Calculate hourly VWAP
        market_open_time = trade_time.replace(hour=9, minute=30, second=0, microsecond=0)
        hour = (trade_time - market_open_time).seconds // 3600
        if stock not in hourly_vwap_dict:
            hourly_vwap_dict[stock] = {hour: []}
        else:
            if hour not in hourly_vwap_dict[stock]:
                hourly_vwap_dict[stock][hour] = []

        hourly_vwap_dict[stock][hour].append((shares, price))

    return tradesdict, hourly_vwap_dict


'''
Main loop for setting input file and parameters.
'''
def main():
    inputFile = gz.open('01302019.NASDAQ_ITCH50.gz', 'rb')
    tradesdict = {}
    hourly_vwap_dict = {}

    # Wait for market open
    wait_for_market_open(inputFile)

    tradesdict, hourly_vwap_dict = parse_messages(inputFile, tradesdict, hourly_vwap_dict)

    # Save results to a text file
    with open('hourly_vwap_results.txt', 'w') as f:
        f.write("Stock,Hour,VWAP\n")  # Header
        for stock, hourly_vwaps in hourly_vwap_dict.items():
            for hour, vwaps in hourly_vwaps.items():
                total_shares = sum(trade[0] for trade in vwaps)
                total_value = sum(trade[0] * trade[1] for trade in vwaps)
                hourly_vwap = total_value / total_shares if total_shares > 0 else 0
                hour_str = f"{hour + 9:02d}:30:00"  # Format hour as HH:MM:SS
                f.write(f"{stock},{hour_str},{hourly_vwap:.4f}\n")  # Format VWAP with 4 decimal places
if __name__ == "__main__":
    main()