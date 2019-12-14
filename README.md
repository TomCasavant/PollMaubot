# Poll Maubot
A plugin for [maubot](https://github.com/maubot/maubot) that creates a poll in a riot room and allows users to vote

## Usage
'!poll new  "Question" "Choice1" "Choice2" "Choice3"' - Creates a new poll with given (at least 1) choices

'!poll results' - Displays the results from the poll

'!poll close' - Ends the poll

Users vote by adding the matching emoji to the poll (i.e. if the first choice has a :thumbsup: then in order to pick that choice the user has to react with :thumbsup:)

## Version 2.0
 - Changed voting format to reactions (instead of '!poll vote')

## Wish List
- Add user configuration to only allow certain users to create polls
- Add auto-timing ability
- Add ability to run multiple polls at once
- Make emojis configurable
- Add placeholder emojis on each poll (to let users just click one)
