import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from datetime import date
import pytz

# Use OAuth2 credentials to authenticate with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet by name
sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")

def getNextID():
  sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")
  return int(sheet.cell(len(sheet.get_all_values()),1).value) + 1
def getID(): 
  sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")
  return int(sheet.cell(len(sheet.get_all_values()),1).value)

def onsiteAdd(date_string, buyer_name, item_name, price):
  sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")
  # get the values of the first empty row in the sheet
  next_row = len(sheet.get_all_values()) + 1

  #get lastest transaction id
  if next_row == 2:
    new_id = 1
  else:  
    new_id = int(sheet.cell(next_row-1,1).value) + 1
  
  # append the data to the sheet
  sheet.update_cell(next_row, 1, new_id)
  sheet.update_cell(next_row, 2, date_string)
  sheet.update_cell(next_row, 3, buyer_name)
  sheet.update_cell(next_row, 4, item_name)
  sheet.update_cell(next_row, 5, price)
  sheet.update_cell(next_row, 6, price)  #set starting bid  (No bidding enabled)
  sheet.update_cell(next_row, 7, "C")  #setting as C for closed
  
def getData():
  sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")
  rows = sheet.get_all_values()

  # Create an empty dictionary to store the data
  data_dict = {}  

  data_dict = {int(row[0]): {"date": row[1], "buyer": row[2], "item_name": row[3], "price": int(row[4].replace(',','')), "start_bid": int(row[5].replace(',','')), "status": row[6]} for row in rows[1:]}

  
  return data_dict

def getDatePST():
  utc_now = datetime.now(pytz.utc)
  return utc_now.astimezone(pytz.timezone('US/Pacific')).strftime('%m/%d/%Y')

def onsiteTotal(raid=None):
    # Open the Google Sheet by name
    sheet = client.open('Coconuts loot tracker_Revised').worksheet("Onsite Sales")

    if raid==None:
        today = getDatePST()
    else:
      try:  
        today=datetime.strptime(raid, '%m/%d/%Y').strftime('%m/%d/%Y')
      except ValueError as e:
        return raid, False

    cell_list = sheet.findall(today)

    if cell_list:
        date_column = sheet.col_values(2)[1:]
        value_column = sheet.col_values(5)[1:]
        total = sum(int(v.replace(',', '')) for i, v in enumerate(value_column) if date_column[i] == today)
        return today, total
    else:
        return today, False 

async def attendance30(context):
    # Open the Google Sheet by name
    sheet = client.open('Coconuts loot tracker_Revised').worksheet("Raid Summaries")
    name_column = sheet.col_values(1)
    value_column = sheet.col_values(2)
    attendance_list=[]
    total_raids = sheet.cell(5,2).value
    
    for i in range(len(value_column)):
        if i>=9 and float(value_column[i].strip('%')) >0:
            name = name_column[i]
            #num_raids=round(float(total_raids) * float(value_column[i].strip('%'))/100)  #pass not including person raid count atm
            entry = f"{name} [{value_column[i]}]"
            attendance_list.append(entry)

    if int(total_raids)>0 and attendance_list:
      await context.send (f'Raid attendance last 30 days (as of {getDatePST()}): [Raid count:**{total_raids}**]')
      list = '\n'.join ((entry) for entry in attendance_list)
      await context.send(f'```{list}```')
    else:
      pass 

async def getStats(context):
    stats = {}
    colValues = client.open('Coconuts loot tracker_Revised').worksheet("Summary Stats").col_values(2)

    #pull stat values
    stats['raidCount'] = colValues[0]
    stats['totalItemsSold'] = colValues[1]
    stats['onsiteItemsSold'] = colValues[2]
    stats['totalSales'] = int(colValues[3].replace(",",""))
    stats['onsiteSales'] = int(colValues[4].replace(",",""))
    stats['totalPayouts'] = colValues[5]
    stats['totalPayoutDue'] = colValues[6]
    stats['lastPayoutDate'] = colValues[7]
    stats['maxPayout'] = colValues[8]
    stats['mains'] = colValues[9]

    output = []
    output.append(f'Total Coconut Raids: {stats["raidCount"]}')
    output.append(f'Active Mains (>25% attendance): {stats["mains"]}')
    output.append(
        f'Total Sales: {stats["totalSales"]:,d}  (Guild Sales: {stats["onsiteSales"]:,d} // Bazaar Sales: {(stats["totalSales"] - stats["onsiteSales"]):,d})')
    output.append(f'Total Payouts to date: {stats["totalPayouts"]}')
    output.append(f'Total Payout due: {stats["totalPayoutDue"]}')
    output.append(f'Last Payout date: {stats["lastPayoutDate"]}')
    output.append(f'Highest Weekly Payout: {stats["maxPayout"]}')

    text = '\n'.join ((line) for line in output)
    await context.send(f'```{text}```')

def lootCheck(item):
    sheet = client.open('Coconuts loot tracker_Revised').worksheet("Loot Input")
    lootData = {}
    qty = 0
    totalSales = 0
    item_col = sheet.col_values(2)
    price_col = sheet.col_values(7)
    seller_col = sheet.col_values(8)
    buyer_col = sheet.col_values(9)
    date_col = sheet.col_values(12)

    for i,name in enumerate(item_col):
        if name == item:
            qty += 1
            try:
                if int(price_col[i].replace(",","")) > 0:
                    lootData[i] = {'buyer':buyer_col[i], 'price':int(price_col[i].replace(",","")),'seller':seller_col[i].strip(),'date':datetime.strptime(date_col[i],'%m/%d/%Y')}
                    totalSales += lootData[i]['price']
            except ValueError as e:
                pass

    # check for latest date for raid drop
    guild_latest = datetime.strptime('01012022','%m%d%Y')
    baz_latest = datetime.strptime('01012022','%m%d%Y')
    maxbaz = 0
    maxguild = 0

    for key in lootData:
        if lootData[key]['seller'].lower() == "onsite":
            if lootData[key]['date'] >= guild_latest:
                guild_latest = lootData[key]['date']
                key_guild = key

            if lootData[key]['price'] >= maxguild:
                maxguild = lootData[key]['price']
                key_maxguild = key
        else:
            if lootData[key]['date'] >= baz_latest:
                baz_latest = lootData[key]['date']
                key_baz = key

            if lootData[key]['price'] >= maxbaz:
                maxbaz = lootData[key]['price']
                key_maxbaz = key

    output = []
    if not lootData:
        output.append('Total drops: N/A')
    else:
      latest_date = lootData[list(lootData.keys())[-1]]['date']  
      output.append(f'Total drops: [{qty}]')  
      output.append(f'Date of last raid drop: [{latest_date.strftime("%m/%d/%Y")}] ')
      output.append(f'Total Sales: [{totalSales:,d}]')
      if maxguild > 0:
          output.append(f'Last guild sale: {lootData[key_guild]["price"]:,d} by {lootData[key_guild]["buyer"]} on {lootData[key_guild]["date"].strftime("%m/%d/%Y")} (Highest: {lootData[key_maxguild]["price"]:,d} by {lootData[key_maxguild]["buyer"]} on {lootData[key_maxguild]["date"].strftime("%m/%d/%Y")})')
      else:
          output.append('Last guild sale: N/A')
      if maxbaz > 0:
          output.append(f'Last Bazaar sale: {lootData[key_baz]["price"]:,d} by {lootData[key_baz]["buyer"]} on {lootData[key_baz]["date"].strftime("%m/%d/%Y")} (Highest: {lootData[key_maxbaz]["price"]:,d} by {lootData[key_maxbaz]["buyer"]} on {lootData[key_maxbaz]["date"].strftime("%m/%d/%Y")})')
      else:
        output.append('Last bazaar sale: N/A')
    output_text = '\n'.join(output)
      
    return output_text



