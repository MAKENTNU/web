# Changelog

A summary of changes made to the codebase, grouped per deployment.


## Unreleased

### New features

- Added [the `django-constance` package](https://django-constance.readthedocs.io/en/stable/)
- Added [a dynamic setting](https://admin.makentnu.no/constance/config/) for hiding/showing the apply ("Søk verv") button in the header

### Improvements

- Updated Django to version 4.1
- Place files uploaded through CKEditor in a separate folder for each model
- Made all pages have a consistent (browser tab) title format
  - Most pages will have " | MAKE NTNU" as suffix to the title;
    subpages of the admin panel have " | Admin panel | MAKE NTNU" as suffix
- Replaced the `trans` template tag with `translate`
- Made the `user` field of `Profile` non-nullable
- Added "and employees" to the end of the Open Graph description
  (shown in some search engines and when embedding pages from the website on sites like Facebook)

### Fixes

- Made the CKEditor file uploader work on all subdomains
- Prevented [CSRF attacks](https://owasp.org/www-community/attacks/csrf) against the logout URL,
  by requiring logout requests being sent using `POST` instead of `GET`

### Other changes

- Set minimum required Python version to 3.10
- Changed order of the apps listed on [the Django admin index page](https://admin.makentnu.no/)
- Never-ending masses of code cleanup


## 2022-10-28 ([#567](https://github.com/MAKENTNU/web/pull/567))

### New features

- Added GitHub Actions workflows for automatically adding issues and PRs to [the repo's project](https://github.com/orgs/MAKENTNU/projects/1)
  and setting adequate "Status" and "Date posted" values

### Improvements

- Improved wording and added image links to the emails sent to users after registering for an event
- Emails are printed to console instead of being sent, when testing or debugging

### Fixes

- Fixed event registration emails not being sent
- Fixed wrong comparison of `MultiLingualTextStructure`
- Fixed `ContentBox.get_absolute_url()` not working
- Fixed unable to submit required search select widgets
  - Which are - among other places - used in the "Add New Member" form


## 2022-07-17 ([#478](https://github.com/MAKENTNU/web/pull/478))

### New features

- Added a URL which always links to the current week for a machine reservation calendar
  - This URL can be copied by right-clicking the "View in calendar" button for a machine on [the machine list page](https://makentnu.no/reservation/),
    and selecting "Copy link address"
- Made machine streams work with the new Raspberry Pi setup
  - Also, only the visible streams are connected to;
    once the page is scrolled so that a stream image is no longer rendered, the stream for that machine is disconnected,
    which makes [the machine list page](https://makentnu.no/reservation/) use considerably less data (depending on how the page is scrolled)
    - This does not apply to the machine detail (calendar) page, as there is always only one stream on the page

### Improvements

- Loading the member list has been made slightly faster
- Renamed a lot of templates (and CSS and JavaScript files) to comply with the style guide
- Improved word breaking (splitting a word between two lines, often using a hyphen) multiple places, like in titles and descriptions
- Added translations to the spreadsheet containing course registrations, that can be downloaded from
  [the course registrations page](https://makentnu.no/reservation/course/)
- Improved the permission check for [the admin panel](https://makentnu.no/admin/)
- Added edit and delete buttons on the machine detail (calendar) page
- On the history page for a documentation page (on [docs.makentnu.no](https://docs.makentnu.no/)),
  the current version link is now a permalink to that specific version

### Fixes

- Fixed endless redirect loop when a logged-in user visited a page that required a permission that the user didn't have
- Fixed error messages for multilingual form fields (like the event "Content" field) not showing
- Previously, editing CKEditor fields (like the event "Content" field) did not prevent the user from leaving the page;
  this has now been fixed
- Fixed sometimes being unable to close fullscreen machine streams, when clicking the close ("X") button
- Fixed old page version warning when visiting the URL for a specific documentation page version which is the current version of that page

### Other changes

- Added setup instructions to the project's README file
- Much code cleanup, yes


## 2022-06-07 ([#461](https://github.com/MAKENTNU/web/pull/461))

### New features

- Added table on [the profile page](https://makentnu.no/checkin/profile/) which displays the completion status of all available courses
  - Also, the profile button in the user dropdown is now visible to all users - not just MAKE members
- Added an internal page titled "[The History of MAKE NTNU](https://i.makentnu.no/make-history/)"
  - This can be found under the new "Misc."/"Diverse" dropdown in the header on the internal site
- Added list of contents to [the equipment list](https://makentnu.no/makerspace/equipment/)
- Added a "Notes" field to machines
  - This is only for internal use and is not displayed anywhere - except for in the machine change form itself, naturally
- Added an "Internal" field to machines
  - This makes machines only visible to and reservable by MAKE members
- Added an "Info message" field to machines
  - This is for displaying information that's useful to know before using the machine, e.g. the filament that the 3D printer uses,
    the needle that's currently inserted in the sewing machine, or just the machine's current state/"mood"
- Added an SLA 3D printer machine type, and an "SLA course" checkbox to course registrations
  - SLA 3D printers are always visible to MAKE members, but only visible to other users after they have taken the SLA course
- Added "bulletin boards" for each committee on [the internal site](https://i.makentnu.no/)
  - These can e.g. contain notices, instructions, and links to common resources, and can act as a "hub" for each committee
- Added an `.editorconfig` file, to make it easier to configure a text editor to format code to (roughly) fit the style guide

### Improvements

- Made [secrets](https://i.makentnu.no/secrets/) only use one language
- Made the place/location text of events more visible
  - This will hopefully reduce the number of people who meet at Makerverkstedet for 3D printer courses, because they didn't see the event's location
- Sorted the news-related templates into folders, and refactored the event detail template into multiple sub-templates
- Improved image sizing and text layout in the [equipment](https://makentnu.no/makerspace/equipment/)
  and [article lists](https://makentnu.no/news/articles/)
- Some minor improvements to the layout of the information text, action buttons and stream image on each machine detail page

### Fixes

- Fixed the machine status text times ("Available for X hours, XX minutes") not being translated to Norwegian

### Other changes

- Renamed the "Advanced course" checkbox to "Raise3D course", and renamed the "Special 3D printers" machine type to "Raise3D printers"
  - This reflects the fact that the course in question is only really for Raise3D printers specifically
  - It also reduces the potential for confusion after having added the SLA course / machine type
    (which can technically also be classified as an "advanced" course / "special" machine type)


## 2022-05-20 ([#453](https://github.com/MAKENTNU/web/pull/453))

### New features

- Added a Docker container for development purposes
- Added [changelog](https://github.com/MAKENTNU/web/blob/main/CHANGELOG.md), issue template and pull request template to
  [our GitHub page](https://github.com/MAKENTNU/web)
- Added button for selecting all shown course registrations
- Added [page for searching through all event participants](https://makentnu.no/admin/news/events/participants/search/)

### Improvements

- Significantly improved page performance when watching streams that fail to connect
  (most notably on [the machine list](https://makentnu.no/reservation/))
- Added warning message when there are gaps between the reservation rules of a machine type
- Reordered [admin panel](https://makentnu.no/admin/) buttons
- The code that reduces the size of uploaded images, now does not use the "reduced" image if it's not actually smaller -
  which could happen with some images

### Fixes

- Fixed server error when users tried to change or delete quotes that they themselves had created
- Fixed a bug that didn't update an end calendar's focused date when changing the date of the start calendar
  (e.g. the start/end time fields on the page for creating a new occurrence for an event)
- Fixed a bug after having selected a time in a calendar popup, which would cause nothing to happen when clicking the input field again
- Fixed server error while reducing the size of an uploaded image that was larger than 2.5 MB
- Fixed server error when uploading an image to an object that had its previous image file deleted - without also updating the database


## 2022-04-07 ([#434](https://github.com/MAKENTNU/web/pull/434) and [#437](https://github.com/MAKENTNU/web/pull/437))

### New features

- Made [the front page of the internal site](https://i.makentnu.no/) editable
  - This only uses Norwegian (not English), and allows editing the HTML source code for extra customization possibilities
- Added an [internal page for quotes](https://i.makentnu.no/quotes/)
- Added more info fields to members (Gmail and MAKE email addresses, starting semester at NTNU, and GitHub, Discord and Minecraft usernames)
- Added history tracking to several models
  (`ContentBox`, `Question`, `Committee`, `Secret`, `MachineUsageRule`, `Event`, `Article` and `InheritanceGroup`)
  - Admins can view this through the Django admin site
- Added translations to [the Django admin site](https://admin.makentnu.no/)
- Added the [`django-extensions`](https://pypi.org/project/django-extensions/)
  and [`django-debug-toolbar`](https://pypi.org/project/django-debug-toolbar/) packages

### Improvements

- Updated Django to version 4.0
- Reordered the buttons in the user dropdown menu
- Added some extra buttons to the CKEditor toolbar
- Most change forms now have a more consistent design, by using the same generic template
- Changed some of the news URLs
  - Redirect URLs have been added for the paths that are commonly linked to from elsewhere
- Redesigned the language button
- Improved the `alt` text (mainly for screen readers) of image links
- Added reduction of the quality of uploaded JPEG files to additional models, like `Equipment`
- Made privileged users always able to register for an event, event if it's sold out
- Made event tickets also display the provided language and comment
- Removed `EventTicket`'s legacy `_name` and `_email` fields
- Event tickets are reactivated instead of recreated
- Added proper title field to content boxes
- The ID of the edited object (e.g. article or event) is now prefixed to the filename when uploading an image
- Added more specific permissions for internal URLs
- Made fonts self-hosted
- Improvements to the change lists and forms of some of the Django admin pages

### Fixes

- Made the course registration list load faster
- Fixed hidden buttons for adding/changing/deleting reservation rules, and for the committee admin panel

### Other changes

- Never-before-seen quanta of code cleanup


## 2022-01-10 ([#402](https://github.com/MAKENTNU/web/pull/402))

### New features

- Added new favicon with better color contrast, and different favicons for the `i`/`internal`/`internt` and `admin` subdomains
- Made "dirtied" (modified) forms prevent the user from leaving
- Added an image description field to articles and events, which is useful for people using screen readers
- Added priority field to secrets
- Added an automatically updated "last modified" field to various models
- Added "Skip to main content" button for navigation using <kbd>Tab</kbd>

### Improvements

- Articles and events are now stored fully in their own separate tables, instead of storing the common fields in a third table
- Small improvements to the design of the event and article pages
- Improved using <kbd>Tab</kbd> for navigating the buttons in the header
- SEO improvements (see [#401](https://github.com/MAKENTNU/web/pull/401))

### Fixes

- Fixed members being unable to have international phone number

### Other changes

- A barely impressive volume of code cleanup


## 2021-10-29 ([#389](https://github.com/MAKENTNU/web/pull/389))

### New features

- Added an [admin page for FAQ categories](https://makentnu.no/faq/admin/categories/)
- For machines with streams: Added a new "no stream" image, in addition to images that are shown when the stream is down *and* the machine has either
  status "Maintenance" or "Out of order"

### Improvements

- Improved layout of the FAQ page and the FAQ question admin page
- Made "My reservations" and "Find free reservation slots" buttons visible when not logged in
- Added Django admin button to user dropdown (visible to users with the "Is staff" status)

### Fixes

- Fixed wrong sorting of members' date joined
- Images for articles, events, etc. are now actually removed on the server when uploading a new image
- Fixed occasionally disappearing course registration rows, which happened when clicking rows after the page had initially loaded
- Fixed a bug that caused the `start_time` field on the "New reservation" form to not be parsed correctly on some iPhones
- Fixed ribbon label on events being displaced by a few pixels

### Other changes

- A respectable quantity of code cleanup


## 2021-10-21 ([#383](https://github.com/MAKENTNU/web/pull/383) and [#385](https://github.com/MAKENTNU/web/pull/385))

### New features

- Machines now have a separate `stream_name` field, for specifying the name that's used to connect to their stream
- Added button for manually hiding shown secrets

### Improvements

- Made the "Rules" buttons on the machine list page more visible
- Change system accesses directly from the member modal
- Improved layout of secrets page
- Improved layout of ticket list
- Improved layout of the reservation list on the "My reservations" and "MAKE NTNU reservations" pages
- MAKE reservations are listed among the creator's own reservations
- Delete/finish reservations without reloading the page
- Added login link to the "New reservation" button
- Improved feedback when reservation is denied
- Made the formatting of times and dates more consistent
- The occurrences of repeating events are not listed one by one anymore on the front page, but are instead listed in a "collapsed" fashion
- Added a "More events" button on the front page, for when there exist more than 4 future events

### Fixes

- Fixed error after registering for an event, which prevented ticket emails from being sent

### Other changes

- Large amounts of code cleanup
- Added code style guide and guideline for code smells


## 2021-05-11 ([#361](https://github.com/MAKENTNU/web/pull/361) and [#367](https://github.com/MAKENTNU/web/pull/367))

### New features

- Added a "Special 3D printers" machine type
  - This is listed on [the machine list (reservations) page](https://makentnu.no/reservation/) when one or more machines of this type have been added
- Added an "Advanced course" checkbox to course registrations
  - Checking this checkbox will grant users permission to create reservations for the special 3D printers
- The course registration form now checks whether the submitted card number is actually (by accident) the phone number of NTNU's Building security
- Changed the URL for the email lists from [/email](https://makentnu.no/email/) to [/about/contact](https://makentnu.no/about/contact/)
- Added a counter at the bottom of [the member list](https://i.makentnu.no/members/)
  and [course registration list](https://makentnu.no/reservation/course/), that shows how many members and course registrations are displayed,
  respectively
- Articles, events, profile pictures and other things you can upload images for, now support GIFs

### Improvements

- Updated Django to version 3.2
- Visiting old URLs that have previously been changed, will redirect to the new URL
  - This applies e.g. to [makentnu.no/rules](https://makentnu.no/rules/), which is written in the old 3D printer course contracts;
    see [the full URL list in the code](https://github.com/MAKENTNU/web/blob/1631cdedddfa204af5b763201027df50ba89e324/web/urls.py#L81-L83)

### Fixes

- (Finally) fixed the course registration list not showing updated info when one or more registrations were modified
- Fixed a bug that prevented sorting and filtering of the member list from both working simultaneously
- Fixed seeing the 404 page when visiting the English "About us" page

### Other changes

- Lots of code cleanup


## 2021-04-13 ([#349](https://github.com/MAKENTNU/web/pull/349))

### New features

- It's now possible to search for users by name in [the member list](https://i.makentnu.no/members/)

### Improvements

- An error message is now shown when uploading an image that is too large

### Fixes

- Fixed the recently discovered issue preventing new users' name from being stored in the database

### Known issues

- Both filtering and sorting the member list simultaneously does currently not work


## 2021-03-10 ([#343](https://github.com/MAKENTNU/web/pull/343))

### New features

- Added an [internal home page](https://i.makentnu.no/) (currently blank)
- Added an [FAQ page](https://makentnu.no/faq/), including the ability to [add questions through the admin page](https://makentnu.no/faq/admin/)

### Fixes

- Fixes for reservations
- Fixes for searching course registrations
- Fixes of other parts of the code

### Other changes

- Code cleanup


## 2020-11-20 ([#334](https://github.com/MAKENTNU/web/pull/334))

### New features

- Added an [internal secrets page](https://i.makentnu.no/secrets/)
- Added [dedicated page for email lists](https://makentnu.no/email/)
- Added support for copying the email addresses of event ticket holders
- Added priority field to equipment

### Other changes

- A lot of fixes
