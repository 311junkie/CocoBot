import httpx
from selectolax.parser import HTMLParser
from gsheets import lootCheck

cookies = {"LucySessionID": "84afcfc6.5f7ef518f58b9"}

def itemLookup(item):
    file_path=r"itemlist.txt"
    item_id, item_name, url = [], [],[]

    with open(file_path,"r") as f:
        lines = f.readlines()
        for line in lines:
            if item.lower() in line.lower():
              id = line.split(",")[0]
              item_id.append(id)
              item_name.append(line.split(",")[1])
              url.append(line.split(",")[-1].strip())
              if item.isdigit() and int(item) == int(id):
                return id, item_name[0], url[0], True
    if item_id:
      return item_id, item_name, url, False
    else:  
      return -1,-1,-1,-1   #item not found

async def getItem(context, message):
  # Split the message into its arguments
  if message == None:
    await context.channel.send("Error - try !lucy <item name>")
    return
    
  #pull item data from lucy  
  item_id, item_name, url, match = itemLookup(message)

  if item_id == -1:
    await context.channel.send(f"Item lookup not found for **[{message}]**.  Try **!item <item name>** or **!item <item id>**")
    return    
  elif len(item_id)>10 and not match:
    await context.channel.send(f'Too many matches found for **{message}** [Matches found: **{len(item_id)}**].  Refine item description and try again.')
  elif len(item_id)>1 and not match:
    await context.channel.send(f'Listing **{len(item_id)}** matches found for **{message}**.  Try !item <item id> or refine item name')
    results = []
    for k,v in enumerate(item_id):
      results.append(f'{k+1}. {item_name[k]} [ID: {item_id[k]}]')
    output_text='\n'.join(results)
    await context.channel.send(f'```{output_text}```')
  else:
    #check for conversion from list to str for url format
    if isinstance(url,list):
      url=url[0]
      item_id=item_id[0]

    resp = httpx.get(url, cookies=cookies)
    
    page = HTMLParser(resp.text)
    item_name = page.css_first('td.shottitle').text().strip()
    item_stats = page.css_first('td.shotdata').text().strip()
    item = f'{item_name}\n{item_stats}'
    
    #check valid return
    await context.send(f'Item stats listed for: **{item_name} [{item_id}]**  ')
    await context.send(f'__**LINK:**__ {url}')
    await context.send(f'```{item_name}\n{item_stats}```')

    #pull coco stats
    cocostats = lootCheck(item_name)
    await context.send(f'__**Coco Loot Statistics [{item_name}]:**__')
    await context.send(f'```{cocostats}```')