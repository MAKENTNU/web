## Proposed changes

<!-- Describe the changes you've made -->


## Areas to review closely

<!-- Refer to areas of the changed code where you would like reviewers to take a closer look -->


## Checklist

_(If any of the points are not relevant, mark them as checked, so that it's easy to see which points you've handled or not)_

- [ ] I've run `makemigrations`, `makemessages` and `compilemessages`
- [ ] I've written tests that fail without these changes (if relevant/possible)
- [ ] I've manually tested the website UI with different device layouts
  - _Most common is to test with typical screen sizes for mobile (320-425 px), tablet (768 px) and desktop (1024+ px), which can easily be done with your browser's dev tools_
- [ ] I've manually tested with different users locally
  - _This can be e.g. anonymous users (i.e. not being logged in), "normal" non-member users, members of different committees, and superusers_
- [ ] I've made sure that my code conforms to [the code style guides](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#code-style-guides)
  - _It's not intended that you read through this whole document, but that you get yourself an overview over its contents, and that you use it as a reference guide / checklist while taking a second look at your code before opening a pull request_
- [ ] I've attempted to minimize the number of [common code smells](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#code-review-guideline-code-smells)
  - _See the comment for the previous checkbox_
- [ ] I've added documentation
  - _E.g. comments, docstrings, or in the [README](https://github.com/MAKENTNU/web/blob/main/README.md)_
- [ ] I've added my changes to the ["Unreleased" section of the changelog](https://github.com/MAKENTNU/web/blob/main/CHANGELOG.md#unreleased), together with a link to this PR
  - _Mainly the changes that are of particular interest to users and/or developers, if any_
- [ ] I've added a "Deployment notes" section above and labelled the PR with [has-deployment-notes](https://github.com/MAKENTNU/web/pulls?q=label%3Ahas-deployment-notes)
  - _...if anything out of the ordinary should be done when deploying these changes to the server (e.g. adding/removing an environment variable, manually creating/changing some objects, running a management command, etc.)_
- [ ] I've structured my commits reasonably
  - _Some tips on this can be found in ["Write Better Commits, Build Better Projects"](https://github.blog/2022-06-30-write-better-commits-build-better-projects/) and in [the code style guides](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#commit-message)_
  - _Restructuring commits after they've already been committed, can be done using e.g. interactive rebase; see [the Git docs on rewriting history](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History)_
