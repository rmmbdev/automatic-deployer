from tempfile import TemporaryDirectory

import git


class GitManipulator:
    _git_url: str | None = None
    _root_directory: str | None = None
    _repo: git.Repo | None = None
    _remote: git.Remote | None = None

    def __init__(self, git_url: str):
        self._git_url = git_url

    def is_repo_valid(self) -> bool:
        try:
            with TemporaryDirectory() as dir_name:
                self._clone_repo(dir_name)
            return True
        except git.GitCommandError as ex:
            if (
                    "does not exist" in ex.stderr or
                    "not found" in ex.stderr or
                    "Logon failed" in ex.stderr
            ):
                return False
            else:
                raise ex

    def setup_repo(self, root_directory: str) -> None:
        self._root_directory = root_directory
        self._clone_repo(self._root_directory)
        self._remote = git.Remote(self._repo, "origin")

    def update_repo(self):
        self._remote.pull(refspec="main")

    def fetch_commits(self, renew=False) -> list[dict]:
        if self._root_directory is None:
            raise Exception("setup_repo first!")

        if renew:
            self._clone_repo(self._root_directory)
        else:
            self.update_repo()

        commits_list = []
        for c in self._repo.iter_commits():
            commits_list.append(
                {
                    "committed_date": c.committed_date,
                    "committed_datetime": c.committed_datetime,
                    "summary": c.summary,
                }
            )
        return commits_list

    def _clone_repo(self, root_directory: str) -> None:
        self._repo = git.Repo.clone_from(url=self._git_url, to_path=root_directory)
