from lib import *


def setup(bot: commands.Bot):
    help = bot.create_group(name="help")

    @help.command(name="commands", description="Get a list of all commands")
    async def commands_list(ctx: commands.Context):
        """Returns a list of all the available commands to the user"""
        await ctx.defer()

        # Retrieve all commands
        all_commands = bot.application_commands

        # Format the commands and their descriptions
        help_text = "## Commands\n"
        for cmd in all_commands:
            help_text += f"- **{cmd.name.capitalize()}**:\n"

            # Check for subcommands
            if hasattr(cmd, "subcommands"):
                for subcmd in cmd.subcommands:
                    help_text += (
                        f" - `/{cmd.name} {subcmd.name}`: {subcmd.description}\n"
                    )
            else:
                help_text += f" - `/{cmd.name}`: {cmd.description}\n"

        # Send the list to the user via DM
        if ctx.guild:
            await ctx.edit("I've sent you a private message!")
            await ctx.author.send(content=help_text)
        else:
            await ctx.edit(content=help_text)

    print("Help group loaded")
