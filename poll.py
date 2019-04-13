import re
from typing import List, Tuple
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command


QUOTES_REGEX = r"\"?\s*?\""  # Regex to split string between quotes

"""
class Config(BaseProxyConfig):
        def do_update(self, helper: ConfigUpdateHelper) -> None:"""


class PollPlugin(Plugin):
    @command.new("poll")
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
            # Show users active poll
            choice_list = "\n".join(
                ["{}. {}".format(x + 1, choices[x]) for x in range(len(choices))]
            )
            response = "{}\n{}".format(question, choice_list)

        await evt.reply(response, html_in_markdown=True)
