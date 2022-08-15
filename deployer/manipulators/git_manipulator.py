from tempfile import TemporaryDirectory

import git
import shutil
import os


class GitManipulator:
    repo_directory: str | None = None
    _git_url: str | None = None
    _repo: git.Repo | None = None
    _remote: git.Remote | None = None
    _branch: str | None = None

    def __init__(
            self,
            git_url: str,
    ):
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
        self.repo_directory = root_directory
        self._clone_repo()
        self._branch = self._repo.heads[0].name
        self._remote = git.Remote(self._repo, "origin")

    def update_repo(self, renew: bool = False):
        if self.repo_directory is None:
            raise Exception("setup_repo first!")

        if renew:
            self._clone_repo()
        else:
            self._remote.pull(refspec=self._branch)

    def fetch_commits(
            self,
            renew: bool = False,
    ) -> list[dict]:
        self.update_repo(renew)
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

    def fetch_tags(
            self,
            renew: bool = False
    ) -> list[dict]:
        self.update_repo(renew)
        tags_list = []
        for t in self._repo.tags:
            tags_list.append(
                {
                    "name": t.name
                }
            )
        return tags_list

    def _clone_repo(self, root_directory: str | None = None) -> None:
        if root_directory is None:
            root_directory = self._get_cleaned_src_folder()

        self._repo = git.Repo.clone_from(url=self._git_url, to_path=root_directory)

    def _get_cleaned_src_folder(self) -> str:
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

        src_path = os.path.join(self.repo_directory, "src")
        # os.remove(src_path)
        try:
            shutil.rmtree(src_path, onerror=onerror)
            os.mkdir(src_path)
        except:
            pass

        return src_path
