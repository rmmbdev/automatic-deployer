import json
import os
import shutil
import time

import typer
from deployer import __app_name__, __version__
from deployer.manipulators import GitManipulator, CommandManipulator
from rich import print
from deployer.consts import (
    ERROR_TEMPLATE,
    COMMAND_UNDONE
)


def main(
        silent: bool = typer.Option(
            default=False,
            help="Execute the command without any output"
        )
):
    if not silent:
        print("Execution details...")
        state["verbose"] = True


def get_app_description() -> str:
    return f"""
    Automatic Deploy CLI app.

    App Name: {__app_name__}\n
    App version: {__version__}\n
    Programmer: Reza Mohammadi
    """


app = typer.Typer(callback=main, help=get_app_description())
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
state = {"verbose": True}


def get_configs() -> dict:
    # load configs
    app_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    with open(os.path.join(app_root, "data", "configs.json"), mode='r') as fh:
        app_configs = json.load(fh)

    return app_configs


def save_configs(new_configs: dict) -> None:
    # load configs
    app_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    with open(os.path.join(app_root, "data", "configs.json"), mode='w') as fh:
        json.dump(new_configs, fh, indent=4, ensure_ascii=False)


def get_oath() -> str:
    return ("\n"
            "    Night gathers, and now my watch begins. \n"
            "    It shall not end until my death. \n"
            "    I shall take no wife, hold no lands, father no children. \n"
            "    I shall wear no crowns and win no glory. \n"
            "    I shall live and die at my post.\n"
            "    I am the sword in the darkness. \n"
            "    I am the watcher on the walls. \n"
            "    I am the fire that burns against the cold,\n the light that brings the dawn,\n"
            " the horn that wakes the sleepers,\n the shield that guards the realms of men. \n"
            "    I pledge my life and honor to the Night’s Watch, for this night and all the nights to come. \n"
            "    G.R.R. Martin")


def get_cleaned_src_folder() -> str:
    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : ``shutil.rmtree(path, onerror=onerror)``
        """
        import stat
        # Is the error an access error?
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    src_path = os.path.join(project_root, "src")
    # os.remove(src_path)
    try:
        shutil.rmtree(src_path, onerror=onerror)
        os.mkdir(src_path)
    except:
        pass

    return src_path


@app.command()
def setup(
        git_url: str = typer.Option(
            default="",
            prompt="Enter git destination url to watch",
            help="Git Repository URL, "
                 "ex [http://gitlab.it/datamining/natural-language-understanding/opinion-news-agancy]"
        ),
        command: str = typer.Option(
            default="",
            prompt="Enter your command",
            help="Bash command, "
                 "ex [gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8200]"
        ),
        run_after_setup: bool = typer.Option(
            default=False,
            prompt="Run One time after setup is completed?",
            help="This will not start the watch!"
        ),
        sleep_interval: int = typer.Option(
            default=2,
            prompt="Sleep interval before two checking",
            help="This parameter value should be considered as in minutes interval. "
                 "Set this parameter for preventing spamming the git server. "
                 "Set the parameter to 0 if it is crucial to check in real time"
        ),
):
    if git_url.strip() == "":
        print(ERROR_TEMPLATE.format("Git Repository URL can not be empty string"))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    if command.strip() == "":
        print(ERROR_TEMPLATE.format("Command can not be empty string"))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    gtm = GitManipulator(git_url)
    is_valid = gtm.is_repo_valid()
    if not is_valid:
        print(ERROR_TEMPLATE.format("Invalid repo url!"))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    if run_after_setup:
        repo_path = get_cleaned_src_folder()
        gtm.setup_repo(repo_path)
        cmm = CommandManipulator(root=True)
        cmm.run("Running Command", command)
        # CommandManipulator.run(command)

    # report
    if state["verbose"]:
        print(f"[magenta]Git Repository URL:[/magenta] [blue]{git_url}[/blue]")
        print(f"[magenta]Execution Command:[/magenta] [blue]{command}[/blue]")
        print(f"[magenta]Sleep Interval:[/magenta] [blue]{sleep_interval}[/blue]")

    # save to file
    new_configs = {
        "setup_done": True,
        "git_repo_url": git_url,
        "execute_command": command,
        "sleep_interval": sleep_interval
    }
    save_configs(new_configs)
    print(f"[green]✔️ Configurations updated![green]")


@app.command()
def start(see_the_oath_and_metaphor_of_the_app: bool = True):
    if see_the_oath_and_metaphor_of_the_app:
        print(get_oath())

    # one time fetching
    configs = get_configs()

    # check for setup done
    if not configs["setup_done"]:
        print(ERROR_TEMPLATE.format("Setup did not run successfully."))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    # clone repo
    gtm = GitManipulator(git_url=configs["git_repo_url"])

    print("Cleaning src folder...")
    repo_path = get_cleaned_src_folder()

    print("Setting up repo handler...")
    gtm.setup_repo(repo_path)

    print("Getting Commits...")
    latest_commits = gtm.fetch_commits()

    # run the command
    cmm = CommandManipulator(root=True)
    cmm.run(message="running command", command=configs["execute_command"])

    sleep_duration = configs["sleep_interval"] * 60
    # watch the repo
    while True:
        print(f"Sleeping for {sleep_duration} seconds")
        time.sleep(sleep_duration)

        print("Fetching new commits...")
        commits = gtm.fetch_commits(renew=False)

        if commits != latest_commits:
            typer.echo("Changes detected in source repository")
            latest_commits = commits

            typer.echo("Running command")
            cmm.run(message="running command", command=configs["execute_command"])


@app.command()
def configs():
    print("deployer configurations")
    print(get_configs(), sep='\n')


@app.command()
def version():
    print(f"App Name: {__app_name__}\nApp version: {__version__}")
