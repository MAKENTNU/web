# Changelog
Description of the changes through deployments.


## Unreleased
### Added
- Changelog, issue template and pull request template.


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
- Added admin page for FAQ categories
- For machines with streams: Added a new "no stream" image, in addition to images that are shown when the stream is down *and* the machine has either status "Maintenance" or "Out of order"

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


## 2021-10-21 ([#383](https://github.com/MAKENTNU/web/pull/383))
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


## 2021-05-11
### Added
- La til en ny maskintype for spesial-3D-printere (som blir lista opp under en egen seksjon på reservasjonssida når noen legger til én eller flere maskiner av den typen)
- Det er nå en "Avansert kurs"-checkbox for kursregistreringer, som kan krysses av på kursregistreringen til en bruker når den har tatt det avanserte printerkurset. (Når brukere har en kursregistrering med denne checkboxen aktivert, gir det dem tilgang til å reservere spesial-3D-printerne)
- Kursregistreringssida sjekker nå om kortnummeret som sendes inn (med et uhell) egentlig er telefonnummeret til Vakt og service (tidl. kjent som Byggsikring)
- Endra URL-en for e-postlistene fra makentnu.no/email til makentnu.no/about/contact
- La til litt tekst på bånn av sida, som sier antall medlemmer som vises i medlemslista og antall registreringer i kursregistreringslista
- Artikler, profilbilder og andre ting man kan laste opp bilder til, støtter nå GIFs

### Changed
- Django oppdatert til 3.2

### Fixed
- Fiksa (endelig) at kursregistreringslista viser oppdatert info når én eller flere registreringer har blitt endra
- Fiksa noen ablegøyer i medlemslista som gjorde at sortering og filtrering ikke fungerte sammen
- Hvis man nå går til noen gamle URL-er som i ettertid har blitt endra på, så vil man bli redirected til den nye URL-en (dette gjelder bl.a. makentnu.no/rules - som står i de gamle kurskontraktene; den fullstendige URL-lista kan ses i denne delen av koden)
- Fiksa at man kom til 404-sida hvis man besøkte den engelske "Om oss"-sida

### Other
- mMMasse kodeopprydding


## 2021-04-13
### Added
- Man kan nå filtrere brukere etter navn i medlemslista

### Changed
- Når man laster opp bilder vil man få en beskjed om bildet er for stort

### Fixed
- Fiksa den nylige feilen som gjorde at nye brukere ikke fikk navnet sitt lagra i databasen

### Known Errors
- både filtrering og sortering ikke fungerer samtidig(en fiks har allerede blitt lagd og kommer til å bli gjort live om ikke så lenge)


## 2021-03-10
### Added
- Intern hjemmeside
- FAQ-side, og mulighet for å legge til spørsmål via administrasjonssiden

### Fixed
- Fikser for reservasjoner
- Fikser for søkefunksjonaliteten til kursregistrering
- Fiks av andre deler av koden

### Other
- Cleanup av kode


## 2020-11-20
### Added
- Secrets kan nå legges ut på internsidene
- Man kan kopiere epostene til folk som er registrert til et arrangement
- Utstyrsprioritert

### Changed
- Oppdatert Epostlisteside

### Other
- En del fixes
