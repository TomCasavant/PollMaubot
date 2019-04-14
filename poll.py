import re
from typing import List, Tuple
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command


QUOTES_REGEX = r"\"?\s*?\""  # Regex to split string between quotes


class Poll:
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices
        self.votes = [0] * len(choices)  # initialize all votes to zero
        self.voters = []
        self.active = True  # Begins the poll
        self.total = 0

    def vote(self, choice, user_id):
        # Adds a vote to the given choice
        self.votes[choice - 1] += 1
        # Adds user to list of users who have already voted
        self.voters.append(user_id)
        self.total += 1

    def isAvailable(self, choice):
        # Checks if given choice is an option
        return choice <= len(self.choices)

    def hasVoted(self, user):
        # Checks if user has already voted
        return user in self.voters

    def isActive(self):
        # Checks if the poll is currently active
        return self.active

    def get_results(self):
        # Formats the results with percentages
        results = "<br />".join(
            [
                f"<tr><td>{choice}:</td> <td>{self.votes[i]}</td><td>{round(self.votes[i]/self.total if self.total else 0,3) * 100}%</td></tr>"
                for i, choice in enumerate(self.choices)
            ]
        )
        results = "<table>" + results + "</table>"
        #results = f"|{self.question}:<br />|" + results
        return results

    def close_poll(self):
        self.active = False


class PollPlugin(Plugin):
    currentPoll = Poll("None", ["None"])

    @command.new("poll", help="Make a poll")
    async def poll(self) -> None:
        pass

    @poll.subcommand("new", help='Creates a new poll with "Question" "choice" "choice" "choice" ...')
    @command.argument(
        "poll_setup",
        pass_raw=True,
        required=True
    )
    async def handler(self, evt: MessageEvent, poll_setup: str) -> None:
        await evt.mark_read()
        r = re.compile(QUOTES_REGEX)  # Compiles regex for quotes
        setup = [
            s for s in r.split(poll_setup) if s != ""
        ]  # Split string between quotes
        question = setup[0]
        choices = setup[1 : len(setup)]
        if len(choices) <= 1:
            response = "You need to enter at least 2 choices."
        else:
            self.currentPoll = Poll(question, choices)
            # Show users active poll
            choice_list = "<br />".join(
                [f"{i+1}. {choice}" for i, choice in enumerate(choices)]
            )
            response = f"{question}<br />{choice_list}"

        await evt.reply(response, html_in_markdown=True)

    @poll.subcommand("vote", help="Votes for an option")
    @command.argument(
        "choice", pass_raw=True, required=True
    )
    async def handler(self, evt: MessageEvent, choice: int) -> None:
        await evt.mark_read()
        # Verify the user is able to vote
        if self.currentPoll.hasVoted(evt.sender):
            await evt.reply("You've already voted in this poll")
        elif not self.currentPoll.isActive():
            await evt.reply("I'm sorry this poll has already ended")
        else:
            # Checks if user entered a valid vote
            if self.currentPoll.isAvailable(int(choice)):
                # Makes the vote
                self.currentPoll.vote(int(choice), evt.sender)
            else:
                await evt.reply("You must enter a valid choice")

    @poll.subcommand("results", help="Prints out the current results of the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        await evt.reply(self.currentPoll.get_results(), html_in_markdown=True)

    @poll.subcommand("close", help="Ends the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        self.currentPoll.close_poll()
        await evt.reply("This poll is now over. Type !poll results to see the results.")
