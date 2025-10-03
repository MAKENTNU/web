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

### 🧳 Developing offline

When running uv commands, pass [the `--offline` flag](https://docs.astral.sh/uv/reference/cli/#uv-run--offline).
For example:
```shell
uv run --offline manage.py runserver
```
</details>


## 🧑‍💻 Contribution guidelines

See [CONTRIBUTING.md](CONTRIBUTING.md) for the following topics:
* [Code style guides](CONTRIBUTING.md#code-style-guides)
* [Code review guideline: Code smells](CONTRIBUTING.md#code-review-guideline-code-smells)


## 📖 [Wiki](https://github.com/MAKENTNU/web/wiki)
[Visit the wiki](https://github.com/MAKENTNU/web/wiki) to read about various things related to development of this project!


## 📝 Changelog

[View the changelog](CHANGELOG.md) to see a list of changes made to the website over time,
as well as a superficial description of the release process.
