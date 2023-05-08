## Proposed changes

<!-- Describe the changes you've made -->


## Areas to review closely

<!-- Refer to areas of the changed code where you would like reviewers to take a closer look -->


## Checklist

_(If any of the points are not relevant, mark them as checked)_

- [ ] Remembered to run the `makemigrations`, `makemessages` and `compilemessages` management commands and committed any changes that should be included in this PR
- [ ] Created tests that fail without the changes, if relevant/possible
- [ ] Manually tested that the website UI works as intended with different device layouts
  - _(Most common is to test with typical screen sizes for mobile (320-425 px), tablet (768 px) and desktop (1024+ px), which can easily be done with your browser's dev tools)_
- [ ] Manually tested that everything works as intended when logged in as different users locally
  - _(This can be e.g. anonymous users (i.e. not being logged in), "normal" non-member users, members of different committees, and superusers)_
- [ ] Made sure that your code conforms to [the code style guides](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#code-style-guides)
  - _(It's not intended that you read through this whole document, but that you get yourself an overview over its contents, and that you use it as a reference guide / checklist while taking a second look at your code before opening a pull request)_
- [ ] Attempted to minimize the number of [common code smells](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#code-review-guideline-code-smells)
  - _(See the comment for the previous checkbox)_
- [ ] Added sufficient documentation - e.g. as comments, docstrings or in the [README](https://github.com/MAKENTNU/web/blob/main/README.md), if suitable
- [ ] Added your changes to the ["Unreleased" section of the changelog](https://github.com/MAKENTNU/web/blob/main/CHANGELOG.md#unreleased) - mainly the changes that are of particular interest to users and/or developers, if any
- [ ] Added a "Deployment notes" section above, if anything out of the ordinary should be done when deploying these changes to the server
- [ ] Structured your commits reasonably
  - _(Some tips on this can be found in ["Write Better Commits, Build Better Projects"](https://github.blog/2022-06-30-write-better-commits-build-better-projects/) and in [the code style guides](https://github.com/MAKENTNU/web/blob/main/CONTRIBUTING.md#commit-message))_
  - _(Restructuring commits after they've already been committed, can be done using e.g. interactive rebase; see [the Git docs on rewriting history](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History))_
