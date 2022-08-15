# Automatic Deployer
A CLI App to watch git repo and automatically run a command (deploy command, ex. build and run docker container) after inspecting some changes.

## Installation
1. Create virtual environment.<br>
    `python -m venv venv`
2. Activate virtual environment.<br>
3. Install package.<br>
   `pip install automatic-deployer`

## Running
### Setup
Use the following command to set up watcher. <br>
Follow the prompt for required inputs. <br>
    `deployer setup`
Or use `--help` to direct accessing the command arguments. <br>
    `deployer setup --help`
### Run
Use the following command to start watching repo up watcher. <br>
    `deployer start`

## Additional Commands
Use `--help` for additional commands and their functionality.

## Notes
* If you want to watch a private repo, you can use the following style git url. <br>
  `https://oauth2:TOKEN@github.com/username/repo.git`
  * TOKEN can be generated throw your vcs. 
## Future Features
* Currently, it only supports `main` branch but in near we will add option to watch other branches too.