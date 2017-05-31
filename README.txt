The robot of Stack Overflow community in Telegram. At this moment, only search
is implemented.

To run it, create a bot account via @BotFather robot in Telegram and activate
inline mode, then set BOT_TOKEN environment variable with the token of your bot.
After that create a SE application on stackapps.com site, and set SO_KEY
environment variable with the key of your app. And at last, install dependencies
using pip, and launch the robot.py script.

#!/bin/bash
export BOT_TOKEN=...
export SO_KEY=...
pip3 install -r requirements.txt
./robot.sh
