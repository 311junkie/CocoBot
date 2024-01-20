import discord
import random
import os
import math
from discord.ext import commands
from keep_alive import keep_alive
from mitch import mitch_joke
from gsheets import onsiteAdd, getID, getData, onsiteTotal, attendance30, getStats, getDatePST
from lucy import getItem

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)
client.remove_command("help")


@client.event
async def on_ready():
  print('Bot is ready')

@client.command()
async def test(context):
  guild = context.guild
  await context.send(context.channel.id)

@client.command()
async def help(context):
  em = discord.Embed(title = "Help", description="Cocobot commands available:")
  em.add_field(name="!summary", value = "Random guild data (Total raids, sales, payouts)")
  em.add_field(name="!attendance",value = "Lists attendance by member over last 30 days")
  em.add_field(name="!item <item name> or <item id>",value = "Item search via Lucy database to display item stats and raid drop statistics")
  if checkChannel(context.channel.id):
    em.add_field(name="!onsite <buyer> <item name> <price>",value="Add onsite item purchase to spreadsheet (bid-bot channel only)")
    em.add_field(name="!totalonsite", value="Returns onsite purchase total for current date Alternate usage: !totalonsite mm/dd/yyyy for specific date (bid-bot channel only)")
  em.add_field(name="!mitch", value="Get a random Mitch Hedberg joke")


  await context.send(embed=em)


#collection of Mitch Hedberg jokes
@client.command()
async def mitch(context, *, message=None):
  error, joke, jokeNum, totalJokes = mitch_joke(message)
  if error == False:
    await context.send(f'> {joke}  -- Mitch Hedberg [{jokeNum}/{totalJokes}]')
  else:
    await context.send(f'Invalid joke number.  Try !mitch [1-{totalJokes}]')

#bidding not used currently
@client.event
async def createbid(ctx, auction):
  guild = ctx.guild
  category = discord.utils.get(guild.categories, name='bidding')
  auction_id = getID()
  buyer = auction[auction_id]["buyer"]
  item_name = auction[auction_id]["item_name"]
  price = auction[auction_id]["price"]
  min_bid = max(math.ceil(price / 10000) * 1000, 5000)
  print(math.ceil(price / 10 / 1000) * 1000)

  channel_name = f"{auction_id}-{item_name}"
  existing_channel = discord.utils.get(guild.channels, name=channel_name)
  if not existing_channel:
    new_channel = await guild.create_text_channel(channel_name,
                                                  category=category)
    await new_channel.send(
      f"Bidding now open for {item_name}.  Opening Bid: {price} by {buyer}.  Minimum bid increment: {min_bid}"
    )
    await getItem(new_channel,item_name)
  else:
    await ctx.send(f"A channel with the name '{channel_name}' already exists.")

#item search command
@client.command()
async def item(context, *, message=None):  
  await getItem(context, message)

#pull 30 days attendance
@client.command()
async def attendance(context):
  await attendance30(context)

#pull quick summary stats
@client.command()
async def summary(context):
  await getStats(context)
  
@client.command()
async def onsite(context):
  pass


def checkChannel(id):
  #check for channel ID's (Rixx test channel or Coco bid bot channel)
    if id==1088611658794021015 or id==1084554954150252594:
      return True
    else:
      return False

@client.event
async def on_message(message):
  #check for bot to not respond to itself
  if message.author == client.user:
    return
    
  #check for command to return onsite sales for today or specified date
  if '!totalonsite' in message.content:
    #check for channel ID's (Rixx test channel or Coco bid bot channel)
    if not checkChannel(message.channel.id):
      return  #skip if outside channel
    args = message.content.split("!totalonsite")[1].strip().split()
 
    if len(args) == 0:
      raid_date, total = onsiteTotal()
    else:
      raid_date, total = onsiteTotal(args[0])

    if total:      
      await message.channel.send(f"```Total onsite sales for  ({raid_date}): {total:,d} plat```")
    else:
      await message.channel.send(f"```No onsite sales found for  ({raid_date}).  Use !totalonsite mm/dd/yyyy format for a specific date```") 
    
  #check for onsite sales entry command
  if '!onsite' in message.content:
    #check for channel ID's (Rixx test channel or Coco bid bot channel)
    if not checkChannel(message.channel.id):
      return  #skip if outside channel
      
    args = message.content.split("!onsite")[1].strip().split()

    if args == "":
      await message.channel.send(
        "Error - try !onsite <buyer name> <item name> <item price>")
      return

      # Check if all three arguments are present
    if len(args) < 3:
      await message.channel.send(
        "Error - try !onsite <buyer name> <item name> <item price>")
      return

    # Extract the arguments
    buyer_name = args[0]
    item_name = " ".join(args[1:-1])
    price = args[-1]

    if any(char.isdigit() for char in buyer_name):
      await message.channel.send(
        "Error - buyer name must not include numbers.  Usage: !onsite <buyer name> <item name> <item price>"
      )
      return

    # Check if the price is a number
    if not price.isdigit():
      await message.channel.send(
        "Error - price must be a number.         Usage: !onsite <buyer name> <item name> <item price>"
      )
      return

    # Call the OnsiteAdd function with the extracted arguments
    onsiteAdd(getDatePST(), buyer_name, item_name, price)
    
    #bidding currently not implemented
    bidding = False
    if bidding:
      auction = getData()
      await createbid(message, auction)
    
    # Send a confirmation message
    await message.channel.send(
      f"Onsite purchase added for {buyer_name}  [{item_name} @ {int(price):,d} plat]")

  await client.process_commands(message)

keep_alive()  #launch webserver to allow auto pings to stay online through uptimerobot.com

TOKEN = os.environ['TOKEN']
client.run(TOKEN)

#if discord commands not working list this under client event section monitoring messages:
#await client.process_commands(message

# #parse itemlist.txt to replace " ;unctuation
# def itemtxt():
#     file_path=r"itemlist.txt"

    
  
#     with open(file_path,"r") as f:
#         data = f.read()
#         data = data.replace('"','')
          

#     file = open(file_path,"w")
#     file.write(data)
#     print('DONE')
  
