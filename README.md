# web
[![build](https://github.com/MAKENTNU/web/workflows/build/badge.svg)](https://github.com/MAKENTNU/web/actions)
[![codecov](https://codecov.io/gh/MAKENTNU/web/graph/badge.svg?token=EL6fslS1y2)](https://codecov.io/gh/MAKENTNU/web)


## 🛠️ Setup

<details>
<summary>Click to expand</summary>

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) (a Python package manager)
1. [Install Git](https://git-scm.com/downloads)
1. Installing a [Git GUI](https://git-scm.com/downloads/guis) is highly recommended, as they allow for much easier and faster visualization of
   the commit structure, and interaction with it, which will help you avoid many common mistakes
   * [Git Extensions](https://gitextensions.github.io/) is an excellent choice, with support for pretty much all Git features you'll ever use - though
     it only runs on Windows, as of time of writing
   * [GitHub Desktop](https://github.com/apps/desktop) works well, but has very limited functionality
1. Clone this repository to your machine
   * Either press a "Clone repository" button in your Git GUI, or run:
     ```shell
     git clone https://github.com/MAKENTNU/web.git
     ```
1. Install dev dependencies:
   (this will create a `.venv` folder inside your repository folder, by default)
   ```shell
   uv sync --group dev
   ```
1. Create an empty `.env` file directly inside the repository folder, and fill it by
   copying the contents of [`.env.example`](.env.example)
1. To be able to run commands in the `Makefile`:
   * If using Windows:
     * Ensure that you have a program installed that can run makefiles.
       This can be done by e.g. installing
       [GnuWin's Make](https://gnuwin32.sourceforge.net/packages/make.htm) using
       [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/):
       ```bash
       winget install GnuWin32.Make
       ```
   * If using Linux/macOS: You don't need to do anything.

#### PyCharm

We recommend using [PyCharm](https://www.jetbrains.com/pycharm/) for development, mostly because of its excellent Django support,
and because it's able to integrate all the IntelliJ-specific settings in [the project's `.editorconfig` file](.editorconfig).

If you decide to use this IDE, open the repo folder cloned as part of the prerequisites, through PyCharm (File → Open...),
and set the following settings (File → Settings...):
* Under "**Python**" → "Django":
  * Make sure the "Enable Django Support" checkbox is checked
  * "Django project root:" `<repo folder location>/src`
  * "Settings:" `web/settings.py`
  * "Manage script:" `<repo folder location>/manage.py`
* Under "**Project Structure**":
  * Mark the `src` folder as "Sources"
* Follow [these instructions](https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html#-r16mz0_87)
  to add the _existing_ uv environment that you created inside the `.venv` folder

### 🚀 Starting the webserver

_We recommend developing using locally installed dependencies, as it's a lot faster and easier to debug, but if you'd like to use Docker (e.g. for
testing stuff in a prod-like environment), follow the instructions under [the "Using Docker" section](#-using-docker) instead._

1. Create an SQLite database file with the proper tables:
   ```shell
   uv run manage.py migrate
   ```
1. Create an admin user for local development:
   ```shell
   uv run manage.py createsuperuser
   ```
   It's easiest to create one with both the username and the password set to "admin", and with no email address.
1. Run the server:
   * If using PyCharm, just press the green "play" button in the top right corner
     * Make sure that the correct run configuration is selected in the dropdown next to the button,
       which by default should be named "web" and have a tiny Django logo
   * Otherwise, run:
     ```shell
     uv run manage.py runserver
     ```

### 🐋 Using Docker

1. [Install Docker desktop](https://www.docker.com/products/docker-desktop/)
1. Create a `.env.docker` file:

   This will contain environment variables that override the ones in `.env`, which will
   be used by code running inside Docker.

   The following file contents is a good basis:
   ```dotenv
   STATIC_AND_MEDIA_FILES__PARENT_DIR='/vol/web/'
   ```
1. Build the Docker image and create the database:
   ```shell
   make d-update
   ```
1. Create an admin user for local development:
   ```shell
   make d-createsuperuser
   ```
1. Run the server:
   * If using PyCharm:
     1. [Add a Docker-based Python interpreter](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html#docker-compose-remote)
        with `make_ntnu` as project name (this should match the `-p` argument in [the `Makefile`](Makefile))
     1. Create a "Django Server" [run configuration](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html) using the newly created
        Python interpreter, with `0.0.0.0` (instead of `localhost`) as host (this should match the IP address specified by the `command` key in
        [`compose.dev.yaml`](docker/compose.dev.yaml))
     1. Press the green "play" button in the top right corner
   * Otherwise, run:
     ```shell
     make d-start
     ```

If you encounter any hard-to-fix Docker-related problems, an easy (but drastic) fix can sometimes be to delete the container (`make d-down`)
and follow the steps above again.

### 🧳 Developing offline

When running uv commands, pass [the `--offline` flag](https://docs.astral.sh/uv/reference/cli/#uv-run--offline).
For example:
```shell
uv run --offline manage.py runserver
# Using the make command:
make start uv_args="--offline"
```
</details>


## 🧹 Linting

<details>
<summary>Click to expand</summary>

Normally, run:
```shell
make lint
```

If you'd like to run a specific hook: (i.e. an `id` key under the `hooks` in
[`.pre-commit-config.yaml`](.pre-commit-config.yaml))
```shell
make lint hook="<hook name>"
```

If you're linting while offline, see [the "Developing offline" section under "Setup"](#-developing-offline).

Alternatively, you can run the command directly for more control - see
[the docs on the `run` command](https://pre-commit.com/#pre-commit-run).
Some examples:

- `uv run pre-commit run` - Runs all hooks against the currently staged files
- `uv run pre-commit run --files "<file path>"`: Runs all hooks against the provided
  file(s)
- `uv run pre-commit run <hook name>` - Runs the `<hook name>` hook against
  the currently staged files
</details>


## 🧑‍💻 Contribution guidelines

See [CONTRIBUTING.md](CONTRIBUTING.md) for the following topics:
* [Code style guides](CONTRIBUTING.md#code-style-guides)
* [Code review guideline: Code smells](CONTRIBUTING.md#code-review-guideline-code-smells)


## 📖 [Wiki](https://github.com/MAKENTNU/web/wiki)
[Visit the wiki](https://github.com/MAKENTNU/web/wiki) to read about various things related to development of this project!


## 📝 Changelog

[View the changelog](CHANGELOG.md) to see a list of changes made to the website over time,
as well as a high-level description of the release process.
