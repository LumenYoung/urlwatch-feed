import os.path
import signal
import sys
import subprocess
from appdirs import AppDirs
from urlwatch.command import UrlwatchCommand
from urlwatch.config import CommandConfig
from urlwatch.main import Urlwatch
from urlwatch.storage import (
    YamlConfigStorage,
    CacheMiniDBStorage,
    CacheRedisStorage,
    UrlsYaml,
)

from typing import List


def run_command(command: List[str]) -> str:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"An error occurred: {error}")
        return str(error)
    else:
        return output.decode()


# if __name__ == "__main__":
#     command = ["urlwatch"]
#     print(run_command(command))

pkgname = "urlwatch"
urlwatch_dir = os.path.expanduser(os.path.join("~", "." + pkgname))
urlwatch_cache_dir = AppDirs(pkgname).user_cache_dir

if not os.path.exists(urlwatch_dir):
    urlwatch_dir = AppDirs(pkgname).user_config_dir

# Check if we are installed in the system already
(prefix, bindir) = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))


# Ignore SIGPIPE for stdout (see https://github.com/thp/urlwatch/issues/77)
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except AttributeError:
    # Windows does not have signal.SIGPIPE
    ...

CONFIG_FILE = "urlwatch.yaml"
URLS_FILE = "urls.yaml"
CACHE_FILE = "cache.db"
HOOKS_FILE = "hooks.py"


def main():
    config_file = os.path.join(urlwatch_dir, CONFIG_FILE)
    urls_file = os.path.join(urlwatch_dir, URLS_FILE)
    hooks_file = os.path.join(urlwatch_dir, HOOKS_FILE)
    new_cache_file = os.path.join(urlwatch_cache_dir, CACHE_FILE)
    old_cache_file = os.path.join(urlwatch_dir, CACHE_FILE)
    cache_file = new_cache_file
    if os.path.exists(old_cache_file) and not os.path.exists(new_cache_file):
        cache_file = old_cache_file

    command_config = CommandConfig(
        sys.argv[1:],
        pkgname,
        urlwatch_dir,
        prefix,
        config_file,
        urls_file,
        hooks_file,
        cache_file,
        False,
    )

    # setup storage API
    config_storage = YamlConfigStorage(command_config.config)

    if any(
        command_config.cache.startswith(prefix) for prefix in ("redis://", "rediss://")
    ):
        cache_storage = CacheRedisStorage(command_config.cache)
    else:
        cache_storage = CacheMiniDBStorage(command_config.cache)

    urls_storage = UrlsYaml(command_config.urls)

    # you can condition list job by changing command_config.list = True
    # TODO how to get this information not from std instead from internal input

    # setup urlwatcher
    urlwatch = Urlwatch(command_config, config_storage, cache_storage, urls_storage)
    urlwatch_command = UrlwatchCommand(urlwatch)
    # run urlwatcher
    urlwatch_command.run()


if __name__ == "__main__":
    main()
