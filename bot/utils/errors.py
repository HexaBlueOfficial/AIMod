"""
All AIMod custom exceptions.
"""

guide = "https://aimod.hexa.blue/guide/errors#"

class AtLeastOneEdit(Exception):
    def __init__(self):
        super().__init__(f"No edits were passed to the command.\n\n**More info:** {guide}AtLeastOneEdit")

class NoOpenAIKey(Exception):
    def __init__(self):
        super().__init__(f"No OpenAI API Key was configured for this guild.\n\n**More info:** {guide}NoOpenAIKey")

class NoRules(Exception):
    def __init__(self):
        super().__init__(f"No rules were configured for this guild.\n\n**More info:** {guide}NoRules")

class GPTResponseProcessingFailed(Exception):
    def __init__(self):
        super().__init__(f"Error in GPT-3.5-turbo response processing.\n\n**More info:** {guide}GPTResponseProcessingFailed")