class NoRefFileFound(Exception):
    def __init__(self, source: str, organization: str, name: str, tag: str, *args):
        super().__init__(*args)

        self.source = source
        self.organization = organization
        self.name = name
        self.tag = tag

    def __str__(self):
        return f"No ref file found for '{self.source}://{self.organization}/{self.name}:{self.tag}'. Please pull model."

class NoGGUFModelFileFound(Exception):
    pass
