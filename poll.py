import re
import random
from typing import List, Tuple
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import (EventType, ReactionEvent)
from maubot import Plugin, MessageEvent
from maubot.handlers import command


QUOTES_REGEX = r"\"?\s*?\""  # Regex to split string between quotes
# [Octopus, Ghost, Robot, Okay Hand, Clapping Hands, Hundred, Pizza Slice, Taco, Bomb, Checquered Flag]
REACTIONS = ["\U0001F44D", "\U0001F44E", "\U0001F419", "\U0001F47B", "\U0001F916", "\U0001F44C", "\U0001F44F", "\U0001F4AF", "\U0001F355", "\U0001F32E", "\U0001F4A3", "\U0001F3C1"]
EMOJI_REGEX = r"^[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]"

class Poll:
    def __init__(self, question, choices, emojis=None):
        self.question = question
        self.choices = choices
        self.votes = [0] * len(choices)  # initialize all votes to zero
        self.voters = []
        self.active = True  # Begins the poll
        self.total = 0

        if emojis:
            self.emojis = []
            reactions_filtered = list(set(REACTIONS).difference(set(emojis)))
            emojis_random = random.sample(reactions_filtered, emojis.count(None))
            for emoji in emojis:
                if emoji:
                    self.emojis.append(emoji)
                else:
                    self.emojis.append(emojis_random.pop())
        else:
            self.emojis = random.sample(REACTIONS, len(choices)) # Select a random assortment of emojis

    def vote(self, choice, user_id):
        # Adds a vote to the given choice
        self.votes[choice] += 1
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
                f"<tr><td>{choice}:</td> <td> {self.votes[i]}</td><td> {round(self.votes[i]/self.total if self.total else 0,3) * 100}%</td></tr>"
                for i, choice in enumerate(self.choices)
            ]
        )
        results = f"{self.question}: <br /> <table>" + results + "</table>"
        return results

    def close_poll(self):
        self.active = False


class PollPlugin(Plugin):
    currentPolls = {}

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
        question = ""
        choices = []
        if poll_setup[0] == '"':
            r = re.compile(QUOTES_REGEX)  # Compiles regex for quotes
            setup = [
                s for s in r.split(poll_setup) if s != ""
            ]  # Split string between quotes
        else:
            setup = re.findall(r"^.*$", poll_setup, re.MULTILINE)
        question = setup[0]
        choices = setup[1:]
        if len(choices) <= 1:
            response = "You need to enter at least 2 choices."
        else:
            emojis = []
            r = re.compile(EMOJI_REGEX)
            for i, choice in enumerate(choices):
                choice_tmp = choice.strip()
                x = r.search(choice_tmp[0])
                if x:
                    emoji = choice_tmp[0]
                    choice_tmp = choice_tmp[1:].strip()
                else:
                    emoji = None
                choices[i] = choice_tmp
                emojis.append(emoji)

            self.currentPolls[evt.room_id] = Poll(question, choices, emojis)
            # Show users active poll
            choice_list = "<br />".join(
                [f"{self.currentPolls[evt.room_id].emojis[i]} - {choice}" for i, choice in enumerate(choices)]
            )
            response = f"{question}<br />{choice_list}"
        self.currentPolls[evt.room_id].event_id = await evt.reply(response, allow_html=True)
        for emoji in self.currentPolls[evt.room_id].emojis:
            await evt.client.react(evt.room_id, self.currentPolls[evt.room_id].event_id, emoji)

    @poll.subcommand("results", help="Prints out the current results of the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        if evt.room_id in self.currentPolls:
            await evt.reply(self.currentPolls[evt.room_id].get_results(), allow_html=True)
        else:
            await evt.reply("There is no active poll in this room", allow_html=True)

    @poll.subcommand("close", help="Ends the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        if evt.room_id in self.currentPolls:
            self.currentPolls[evt.room_id].close_poll()
            await evt.reply("This poll is now over. Type !poll results to see the results.")
        else:
            await evt.reply("There is no active poll in this room")

    @command.passive(regex=EMOJI_REGEX,
                     field=lambda evt: evt.content.relates_to.key,
                     event_type=EventType.REACTION, msgtypes=None)
    async def get_react_vote(self, evt: ReactionEvent, _: Tuple[str]) -> None:
        if (evt.content.relates_to.event_id == self.currentPolls[evt.room_id].event_id): # Is this on the correct message?
            if not self.currentPolls[evt.room_id].hasVoted(evt.sender): # has the user already voted?
                if (evt.content.relates_to.key in self.currentPolls[evt.room_id].emojis): # Is this a possible choice?
                    self.currentPolls[evt.room_id].vote(self.currentPolls[evt.room_id].emojis.index(evt.content.relates_to.key), evt.sender) # Add vote/sender to poll
