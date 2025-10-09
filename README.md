# web
[![build](https://github.com/MAKENTNU/web/workflows/build/badge.svg)](https://github.com/MAKENTNU/web/actions)
[![codecov](https://codecov.io/gh/MAKENTNU/web/graph/badge.svg?token=EL6fslS1y2)](https://codecov.io/gh/MAKENTNU/web)


## Setup

<details>
<summary>Click to expand</summary>

### Prerequisites

* [Git](https://git-scm.com/downloads)
  * Using a [Git GUI](https://git-scm.com/downloads/guis) is highly recommended, as they allow for much easier and faster visualization of the commit
    structure, and interaction with it, which will help you avoid many common mistakes
    * [Git Extensions](https://gitextensions.github.io/) is a good choice - though it only runs on Windows, as of time of writing
* Python **3.10**+ (latest, stable version preferred)
* Having cloned this repository to your machine
  * Either press a "Clone repository" button in your Git GUI, or run:
    ```shell
    git clone https://github.com/MAKENTNU/web.git
    ```

#### PyCharm

We recommend using [PyCharm](https://www.jetbrains.com/pycharm/) for development, mostly because of its excellent Django support,
and because it's able to integrate all the IntelliJ-specific settings in [the project's `.editorconfig` file](.editorconfig).

If you decide to use this IDE, open the repo folder cloned as part of the prerequisites, through PyCharm (File → Open...),
and set the following settings (File → Settings...):
* Under "**Languages & Frameworks**" → "Django":
  * Make sure the "Enable Django Support" checkbox is checked
  * "Django project root:" `<repo folder location>/src`
  * "Settings:" `web/settings.py`
  * "Manage script:" `<repo folder location>/manage.py`
* Under "**Project: \<repo folder name\>**" → "Project Structure":
  * Mark the `src` folder as "Sources"

### Installation

1. Create a virtual environment, presumably named `venv`:
   * This should be placed in the folder *containing* the project folder, and not inside the project folder itself
     * Example folder structure (where `web` is the name of the project folder):
       ```
       MAKE
       ├─ venv
       └─ web
          └─ README.md (this file)
       ```
     * Among other things, this prevents translations from being made inside the virtual environment folder
       when running the `makemessages` management command
     * If using PyCharm, and a virtual environment was not created as part of the project creation process, refer to
       [the "Configure a virtual environment" guide](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html#python_create_virtual_env)
     * Otherwise, `cd` to the project folder, and run:
       ```shell
       [newest installed Python command, like python3.11] -m venv ../venv
       ```
1. Activate the virtual environment:
   * If using PyCharm, this should be done automatically when opening a terminal tab inside the IDE
   * Otherwise, `cd` to the project folder, and run:
     * On Windows:
       ```shell
       ..\venv\Scripts\activate
       ```
     * On Linux/macOS:
       ```shell
       source ../venv/bin/activate
       ```
1. Install requirements:
   * If using Windows, first download the correct wheel for the [`python-ldap`](https://pypi.org/project/python-ldap/) package
     from [Christoph Gohlke](https://github.com/cgohlke)'s [python-ldap-build repository](https://github.com/cgohlke/python-ldap-build).
     and install it:
     ```shell
     pip install [path to .whl file]
     ```
     (It is possible to instead build `python-ldap` from source, but it's a bit cumbersome setting up the right build tools.)
   * Regardless of operating system, run:
     ```shell
     pip install -r requirements.txt
     ```

### Running the server for the first time

1. Create an SQLite database file with the proper tables:
   ```shell
   python manage.py migrate
   ```
1. Create an admin user for local development:
   ```shell
   python manage.py createsuperuser
   ```
   It's easiest to create one with both the username and the password set to "admin", and with no email address.
1. Run the server:
   * If using PyCharm, just press the green "play" button in the top right corner
     * Make sure that the correct run configuration is selected in the dropdown next to the button,
       which by default should be named "web" and have a tiny Django logo
   * Otherwise, run:
     ```shell
     python manage.py runserver [optional port number; defaults to 8000]
     ```
</details>


## Contribution guidelines

See [CONTRIBUTING.md](CONTRIBUTING.md) for the following topics:
* [Code style guides](CONTRIBUTING.md#code-style-guides)
* [Code review guideline: Code smells](CONTRIBUTING.md#code-review-guideline-code-smells)


## [Wiki](https://github.com/MAKENTNU/web/wiki)
[Visit the wiki](https://github.com/MAKENTNU/web/wiki) to read about various things related to development of this project!


## Changelog

[View the changelog](CHANGELOG.md) to see a list of changes made to the website over time,
as well as a superficial description of the release process.
