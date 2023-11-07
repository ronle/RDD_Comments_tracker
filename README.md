# RDD_Comments_tracker
This bot listens to spre-specified subreddit and checks for any comment containing specific keywords.
The posting which comply with the criteria will then be collected in external JSON file under the same folder as the application
Triggers list is stored in 

usage example:
python RDD_Comments_tracker.py -s all -t triggersList.txt

-s: name of subreddit to track
-t: name of triggers list file 

Default values:
-s = test
-t triggersList.exe
