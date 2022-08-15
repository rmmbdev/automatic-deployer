"""This module provides the Automatic Deployer CLI."""

import json
import os
import time

import typer
from deployer import __app_name__, __version__
from deployer.consts import (
    ERROR_TEMPLATE,
    COMMAND_UNDONE,
    COMMAND_HINT,
    COMMAND_SUCCESSFUL,
    OATH
)
from deployer.manipulators import GitManipulator, CommandManipulator
from rich import print


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
    return OATH


@app.command()
def setup(
        git_url: str = typer.Option(
            default="",
            prompt="Enter git destination url to watch",
            help="Git Repository URL, "
                 "ex [http://gitlab.it/datamining/natural-language-understanding/opinion-news-agancy]"
        ),
        track_commits: bool = typer.Option(
            default=True,
            prompt="Enable tracking commits in watcher?",
        ),
        track_tags: bool = typer.Option(
            default=False,
            prompt="Enable tracking tags in watcher?",
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

    # if both track_commits and track_tags are False
    if (not track_commits) and (not track_tags):
        print(ERROR_TEMPLATE.format("At least one of `track-commits` or `track-tags` should be set for watch"))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    gtm = GitManipulator(git_url)
    is_valid = gtm.is_repo_valid()
    if not is_valid:
        print(ERROR_TEMPLATE.format("Invalid repo url!"))
        print(COMMAND_UNDONE)
        raise typer.Exit()

    if run_after_setup:
        gtm.setup_repo(project_root)
        cmm = CommandManipulator(run_as_root=True)
        cmm.run(message="Running Command", command=command, repo_directory=gtm.repo_directory, show_output=True)

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
        "sleep_interval": sleep_interval,
        "track_commits": track_commits,
        "track_tags": track_tags
    }
    save_configs(new_configs)
    print(COMMAND_SUCCESSFUL.format("Configurations updated!"))


@app.command()
def start(
        see_the_oath_and_metaphor_of_the_app: bool = True,
        verbose: bool = typer.Option(default=False, ),
):
    # one time fetching
    configs = get_configs()

    # check for setup done
    if not configs["setup_done"]:
        print(ERROR_TEMPLATE.format("Setup did not run successfully."))
        print(COMMAND_HINT.format("deployer setup"))
        raise typer.Exit()

    if see_the_oath_and_metaphor_of_the_app:
        print(get_oath())

    # clone repo
    gtm = GitManipulator(git_url=configs["git_repo_url"])

    print("Cleaning src folder...")

    print("Setting up repo handler...")
    gtm.setup_repo(project_root)

    print("Getting Commits and Tags...")
    latest_commits = gtm.fetch_commits()

    if configs["track_tags"]:
        latest_tags = gtm.fetch_tags(renew=True)
    else:
        latest_tags = gtm.fetch_tags(renew=False)

    # run the command
    cmm = CommandManipulator(run_as_root=True)
    cmm.run(
        message="running command",
        command=configs["execute_command"],
        repo_directory=gtm.repo_directory,
        show_output=verbose
    )

    sleep_duration = configs["sleep_interval"] * 60
    # watch the repo
    while True:
        print(f"Sleeping for {sleep_duration} seconds")
        time.sleep(sleep_duration)

        print("Fetching new changes...")
        commits = []
        if configs["track_commits"]:
            commits = gtm.fetch_commits(renew=False)

        tags = []
        if configs["track_tags"]:
            tags = gtm.fetch_tags(renew=True)

        if (commits != latest_commits) or (tags != latest_tags):
            typer.echo("Changes detected in source repository")
            latest_commits = commits
            latest_tags = tags

            typer.echo("Running command")
            cmm.run(
                message="running command",
                command=configs["execute_command"],
                repo_directory=gtm.repo_directory,
                show_output=verbose
            )


@app.command()
def reset(
        sure: bool = typer.Option(
            default=False,
            prompt="Are you sure?",
        ),
):
    if sure:
        new_configs = {
            "setup_done": False,
        }
        save_configs(new_configs)
        print(COMMAND_SUCCESSFUL.format("Configurations Reset!"))
    else:
        print(COMMAND_UNDONE)


@app.command()
def configs():
    print("deployer configurations")
    print(get_configs(), sep='\n')


@app.command()
def version():
    print(f"App Name: {__app_name__}\nApp version: {__version__}")
