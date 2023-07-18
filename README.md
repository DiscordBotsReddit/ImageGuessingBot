# ImageGuessingBot
Discord.py bot to hold guessing games for images.

https://discord.com/api/oauth2/authorize?client_id=1130923435724382239&permissions=274877909056&scope=bot

---

Required permissions:

- `Send Messages` - To send messages

- `Send Messages in Threads`- To give you the option of keeping the quiz in a ForumChannel Thread

- `Add Reaction` - Adds a ✅ to the winning message.

---

Current commands:

- `/new solution image` - Adds a new image to the guessing database.  The solution provided is case-sensitive (`flower` is not the same as `Flower`).  Supports images and gifs.

- `/remove word` - Removes an image from the guessing database.  `word` will autocomplete based on your current database entries and what you have typed so far.

- `/start` - Starts a new guessing game.  Everyone has 30 seconds to find the correct word, or the game ends.  There is a 3 second delay between rounds.

- `/end` - Ends the current guessing game.  (Current known bug: If you end the game during a round, the game timeout message will still show after 30 seconds)
