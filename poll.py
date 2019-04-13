import re
from typing import List, Tuple
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command


QUOTES_REGEX = r"\"?\s*?\""  # Regex to split string between quotes

"""
class Config(BaseProxyConfig):
        def do_update(self, helper: ConfigUpdateHelper) -> None:"""


class Poll:
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices
        self.votes = [0] * len(choices)  # initialize all votes to zero
        self.voters = []
        self.active = True

    def vote(self, choice, user_id):
        self.votes[choice-1] += 1
        self.voters.append(user_id)

    def isAvailable(self, choice):
        return choice <= len(self.choices)

    def hasVoted(self, user):
        return user in self.voters

    def isActive(self):
        return self.active

    def get_results(self):
        results = "<br />".join(
            [f"{choice}: {self.votes[i]}" for i, choice in enumerate(self.choices)]
        )
        return results

    def end_poll(self):
        self.active = False


class PollPlugin(Plugin):
    currentPoll = Poll("None", ["None"])

    @command.new("poll", help="Make a poll")
    async def poll(self) -> None:
        pass

    @poll.subcommand("new")
    @command.argument("poll_setup", pass_raw=True, required=True)
    async def handler(self, evt: MessageEvent, poll_setup: str) -> None:
        await evt.mark_read()
        r = re.compile(QUOTES_REGEX)
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

    @poll.subcommand("vote")
    @command.argument("choice", pass_raw=True, required=True)
    async def handler(self, evt: MessageEvent, choice: int) -> None:
        await evt.mark_read()
        if self.currentPoll.hasVoted(evt.sender):
            await evt.reply("You've already voted in this poll")
        elif not self.currentPoll.isActive():
            await evt.reply("I'm sorry this poll has already ended")
        else:
            if self.currentPoll.isAvailable(int(choice)):
                self.currentPoll.vote(int(choice), evt.sender)
            else:
                await evt.reply("You must enter a valid choice")

    @poll.subcommand("results")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        await evt.reply(self.currentPoll.get_results(), html_in_markdown=True)


    @poll.subcommand("end")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        self.currentPoll.end_poll()
        await evt.reply("This poll is now over. Type !poll results to see the results.")
