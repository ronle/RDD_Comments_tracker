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
parser.add_argument("-s","--subReddit", nargs='?', default="all")
parser.add_argument("-t","--triggers", nargs='?', default="triggersList.txt")

args = parser.parse_args()
subRedditStr = args.subReddit
triggersFileName = args.triggers

#open triggersList.txt file and prepare the list element
file = open(triggersFileName, "r")
triggersList = file.readlines()
triggersList = [line.strip() for line in triggersList] # Strip whitespace characters from each line
triggersList = [word.lower() for word in triggersList]

print("Listening to [" + subRedditStr +"] subReddit")
print("Triggers to look for: ",triggersList)

#Keep running after exception error
carryOn = True

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

# Initialize the date variables to be used in file names
# and for creating new files at end of each day
prev_date = datetime.date.today()

jsonFileName = 'outJsonFile' + prev_date.strftime("%Y%m%d") +'.json'
logFileName = 'log' + prev_date.strftime("%Y%m%d") +'.txt'

#create logger and open initial log file
logging.basicConfig(level=logging.ERROR, filename=logFileName, filemode='a')

# Get the logger object
logger = logging.getLogger()

# Define a function that changes the log file name
def change_log_file(new_filename):
    # Get the old file handler
    old_handler = logger.handlers[0]
    # Close the old file handler
    old_handler.close()
    # Remove the old file handler from the logger
    logger.removeHandler(old_handler)
    # Create a new file handler with the new file name
    new_handler = logging.FileHandler(new_filename, mode='a')
    # Set the logging level and the formatter for the new file handler
    new_handler.setLevel(logging.ERROR)
    new_handler.setFormatter(old_handler.formatter)
    # Add the new file handler to the logger
    logger.addHandler(new_handler)


#handle any file writes needed
def handleFile(dataToWrite, fileName):
    with open(fileName, 'w') as f:
        json.dump(dataToWrite, f)
    

#check if json file exist in the script path
#if not, a file is created and initial template record is created.
def writeTemplate(fileName):
    with open(fileName, 'w') as f:
        template = textwrap.dedent("""
        [
            {
            "id": 1,
            "author_name": "John Doe",
            "author_id": "JohnDoe",
            "subReddit": "test",
            "commentsList":[
                "None"
                ]
            }
        ]
        """)
        f.write(template)
    f.close()
        
while carryOn:
    curr_date = datetime.date.today() 
      
    if curr_date != prev_date:
        jsonFileName = 'outJsonFile' + curr_date.strftime("%Y%m%d") +'.json'
        newLogFileName = 'Log' + curr_date.strftime("%Y%m%d") +'.txt'
        change_log_file(newLogFileName)
        prev_date = curr_date
          
    try:    
        with open(jsonFileName, 'a+') as rf: # Opens json in all actions allowed mode    
            if not os.path.getsize(jsonFileName) == 0:
                data = json.load(rf)
            else:
               writeTemplate(jsonFileName) 
               
            # Begins the comment stream, scans for new comments
            # listent to the specific mentioned subreddit (in this case "All")
            for comment in reddit.subreddit(subRedditStr).stream.comments(skip_existing=True):
            
                # for every new comment detected, instantiate the following variables:         
                reddit_author_name = str(comment.author.name) # Fetch author name
                reddit_author_id = str(comment.author.id) # Fetch author id
                reddit_comment_lower = comment.body.lower() # Fetch comment body and convert to lowercase
                subReddit = str(comment.submission.subreddit)
                            
                if any(word in reddit_comment_lower for word in triggersList): #Checks for keywords in comment
                    
                    #Terminal print
                    print("##### NEW COMMENT #####")
                    print(comment.author)
                    print(comment.author.id)    
                    print(comment.body.lower())
                    print(comment.submission.subreddit)
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
                            "subReddit": subReddit,
                            "commentsList": [
                                reddit_comment_lower
                                ]
                            }
                        data.append(newRecord)
                        handleFile(data, jsonFileName)
    # except FileNotFoundError:
    #     createNewFile()
        
    except KeyboardInterrupt:
        carryOn = False
        handleFile(data, jsonFileName)
        logger.close()
        sys.exit(0)

    except Exception as e: # in case of major error, log that error into log file
        logger.error(e)
        time.sleep(60)
