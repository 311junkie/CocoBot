#jokes 1 to 250  https://www.buzzfeed.com/mrloganrhoades/a-complete-ranking-of-almost-every-single-mitch-hedberg-
#modified joke list from https://github.com/kyledhebert/mitch-hedberg-rest/tree/master

import random

def mitch_joke(jokeNum=None):
  error = False
  joke, index = 0,0
  joke_list  = []
  
  #set and open txt file
  file_path=r"mitch.txt"
  
  with open(file_path,"r") as f:
    lines = f.readlines()
    for line in lines:
      joke_list.append(line.replace("\n",""))

  if jokeNum == None:
    joke = random.choice(joke_list)
    index = joke_list.index(joke)+1  
  elif not jokeNum.isdigit():
    error = True
  elif int(jokeNum) >0 and int(jokeNum) <= len(joke_list):
    joke = joke_list[int(jokeNum)-1]
    index = jokeNum
  else:
    error = True
  
  return error, joke, index, len(joke_list)

