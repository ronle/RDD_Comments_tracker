# This file will connect to specific subreddit and "listen" to provided comments
# Once a comment with specific triggers is detected, it will log that message to json file
# for ease of future lookup. If this is new comment of existing logged user, the comment will be appended to that same user

import logging
import praw
import json
import os
import datetime
import time
import argparse
import sys
import textwrap


#instantiate command line runtime
parser = argparse.ArgumentParser(
    prog="RDD_Comments_tracker",
    description='This program listens to specific subreddit and collect all comments with specific keywords',
    argument_default=argparse.SUPPRESS
)
parser.add_argument("-s","--subReddit", nargs='?', default="test")
parser.add_argument("-t","--triggers", nargs='?', default="triggersList.txt")

args = parser.parse_args()
subRedditStr = args.subReddit
triggersFileName = args.triggers

#open triggersList.txt file and prepare the list element
file = open(triggersFileName, "r")
triggersList = file.readlines()
triggersList = [line.strip() for line in triggersList] # Strip whitespace characters from each line

print("Listening to [" + subRedditStr +"] subReddit")
print("Triggers to look for: ",triggersList)

#Keep running after exception error
carryOn = True

# Initialize the previous date as the current date
prev_date = datetime.date.today()

# All reddit bot IDs should go into "Credentials.json" file
credentials = 'credentials.json'
with open(credentials) as f:
    creds = json.load(f)
    bot_id = creds["username"]    

# Connecting your bot to your personal script app and logging in
reddit = praw.Reddit(
    client_id=creds['client_id2'],
    client_secret=creds['client_secret2'],
    username = creds['username'],
    password = creds['password'],
    user_agent = creds['user_agent']
    )

jsonFileName = 'outJsonFile' + prev_date.strftime("%Y%m%d") +'.json'
logFileName = 'log' + prev_date.strftime("%Y%m%d") +'.txt'

#handle any file writes needed
def handleFile(dataToWrite, fileName):
    with open(fileName, 'w') as f:
        json.dump(dataToWrite, f)
    

#check if json file exist in the script path
#if not, a file is created and initial template record is created.
if not os.path.exists(jsonFileName):
    with open(jsonFileName, 'w') as f:
        template = textwrap.dedent("""
        [
            {
            "id": 1,
            "author_name": "John Doe",
            "author_id": "JohnDoe",
            "commentsList":[
                "None"
                ]
            }
        ]
        """)
        
        f.write(template)
        f.close()


while carryOn:
    
    logger = logging.getLogger ('mylogger') #Create a logger object
    logger.setLevel (logging.ERROR)         #Set the logging level to ERROR   
    fh = logging.FileHandler (logFileName)    #Create a file handler object
    formatter = logging.Formatter ('%(asctime)s - %(levelname)s - %(message)s') #Create a formatter object
    fh.setFormatter (formatter)             #Set the formatter for the file handler
    logger.addHandler (fh)                  #Add the file handler to the logger
    
    with open(jsonFileName, 'r') as rf: # Opens json in all actions allowed mode    
        data = json.load(rf)
    
        curr_date = datetime.date.today()

        try:    
        
            # Begins the comment stream, scans for new comments
            # listent to the specific mentioned subreddit (in this case "All")
            for comment in reddit.subreddit(subRedditStr).stream.comments(skip_existing=True):
            
                # for every new comment detected, instantiate the following variables:         
                reddit_author_name = str(comment.author.name) # Fetch author name
                reddit_author_id = str(comment.author.id) # Fetch author id
                reddit_comment_lower = comment.body.lower() # Fetch comment body and convert to lowercase
                            
                if any(word in reddit_comment_lower for word in triggersList): #Checks for keywords in comment
                    
                    #Terminal print
                    print("##### NEW COMMENT #####")
                    print(comment.author)
                    print(comment.author.id)    
                    print(comment.body.lower())
                    print("           ")
                    
                    #check if OP is already in data file
                    try:
                                
                        match = next(user for user in data if user['author_id'] == reddit_author_id) #Checks if OP already exist in data file
                        
                        if reddit_comment_lower not in match['commentsList']: #record with same user already exist, adding the new comment
                            match["commentsList"].append(reddit_comment_lower)            

                    except: #Record does not exist, write new record to JSON file
                        
                        last_id = max(data, key=lambda x: x['id']) #find the last record ID created 
                        newRecord = {
                            "id": last_id['id']+1,      #Increment that by one and append as the new comment ID
                            "author_name": reddit_author_name,
                            "author_id": reddit_author_id,
                            "commentsList": [
                                reddit_comment_lower
                                ]
                            }
                        data.append(newRecord)
                        handleFile(data, jsonFileName)
        
        except KeyboardInterrupt:
            carryOn = False
            handleFile(data, jsonFileName)
            fh.close()
            sys.exit(0)

        except Exception as e: # in case of major error, log that error into log file
            logger.exception(e)
            time.sleep(20)
            
    if curr_date != prev_date:
        handleFile(data, jsonFileName)
        fh.close()
        jsonFileName = 'outJsonFile' + curr_date.strftime("%Y%m%d") +'.json'
        logFileName = 'log' + curr_date.strftime("%Y%m%d") +'.txt'
        prev_date = curr_date

fh.close()