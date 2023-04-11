"""
All Views used.
"""

import discord
from discord import ui

class FlagLog(ui.View):
    def __init__(self):
        super().__init__(timeout=None)