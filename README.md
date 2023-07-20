# ImageGuessingBot 🎨
Discord.py bot to hold guessing games for images.

Idea came from:  https://www.reddit.com/r/discordbot/comments/152yv72/discord_image_quizz_bot/

https://discord.com/api/oauth2/authorize?client_id=1130923435724382239&permissions=274877909056&scope=bot

## Required permissions:

- `Send Messages` - To send messages

- `Send Messages in Threads`- To give you the option of keeping the quiz in a ForumChannel Thread

- `Add Reaction` - Adds a ✅ to the winning message.

## Current commands:

- `/new solution databank image` - Adds a new image to the guessing database grouped by `databank`.  The solution provided is case-sensitive (`flower` is not the same as `Flower`).  Supports images and gifs.

- `/update solution [new_solution] [new_image] [new_bank]` - Updates the solution in your database.  All parameters are optional.

- `/copy solution old_bank new_bank` - Copies the solution to a new bank.  Add a solution with `/new` to create the new bank if needed.

- `/remove word databank` - Removes an image from the guessing database.  The options for `word` and `databank` will autocomplete based on your current database entries and what you have typed so far.

- `/start databank [timeout]` - Starts a new guessing game with images from your `databank`.  Everyone has `timeout` seconds (defaults to 30) to find the correct word, or the game ends.  There is a 3 second delay between rounds.

- `/end` - Ends the current guessing game.

- `/user reset_points member double_check` - Resets the given server member's points to 0 (zero).  Requires you to have the `Ban Members` or `Administrator` permissions to run.  `double_check` accepts `no | yes` and must be `yes` to reset the points.



If you're enjoying Image Guesser, please consider leaving a review on Top.gg!

https://top.gg/bot/1130923435724382239#reviews
