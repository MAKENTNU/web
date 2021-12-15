# Contribution guidelines

## Table of contents
- [Code style guides](#code-style-guides)
- [Code review guideline: Code smells](#code-review-guideline-code-smells)


------------------------------------------------------------------------------------------------------------------------------------------------------


# Code style guides

## Table of contents
* [Global](#global)
  + [Max line length](#max-line-length)
  + [Empty/blank lines](#emptyblank-lines)
  + [MAKE vs. the word "make"](#make-vs-the-word-make)
* [Git](#git)
  + [Branch name](#branch-name)
  + [Commit message](#commit-message)
* [Python](#python)
  + [For code in general](#for-code-in-general)
    - [PEP8](#pep8)
    - [String quotation marks](#string-quotation-marks)
    - [Quotation marks inside strings](#quotation-marks-inside-strings)
    - [String concatenation](#string-concatenation)
    - [Trailing commas](#trailing-commas)
    - [Operator wrapping](#operator-wrapping)
    - [Imports](#imports)
  + [For each module (file)](#for-each-module-file)
    - [Empty/blank lines](#emptyblank-lines-1)
    - [Folder/directory location](#folderdirectory-location)
    - [Filename](#filename)
      + [Migration filename](#migration-filename)
  + [For each class](#for-each-class)
    - [Class name](#class-name)
    - [Field and method order](#field-and-method-order)
  + [For each view class](#for-each-view-class)
    - [View class name](#view-class-name)
    - [View class order](#view-class-order)
    - [View field order](#view-field-order)
  + [For each function/method](#for-each-functionmethod)
    - [Function/method name](#functionmethod-name)
  + [For each URL path](#for-each-url-path)
    - [(Endpoint) path/route](#endpoint-pathroute)
    - [Path name](#path-name)
    - [Path order](#path-order)
    - [`urlpatterns` organization](#urlpatterns-organization)
      + [`urlpatterns` for admin/API view paths](#urlpatterns-for-adminapi-view-paths)
  + [For each variable/field](#for-each-variablefield)
    - [Variable/field name](#variablefield-name)
    - [Model field definition arguments](#model-field-definition-arguments)
      + [Model field keyword argument order](#model-field-keyword-argument-order)
      + [Model field argument value](#model-field-argument-value)
* [Django templates / HTML / CSS](#django-templates--html--css)
  + [For code in general](#for-code-in-general-1)
    - [String quotation marks](#string-quotation-marks-1)
    - [Hex (color) code literals](#hex-color-code-literals)
  + [For each file](#for-each-file)
    - [Empty/blank lines](#emptyblank-lines-2)
    - [Filename](#filename-1)
      + [Django template filenames](#django-template-filenames)
      + [CSS filenames](#css-filenames)
  + [For each template block](#for-each-template-block)
    - [Block order](#block-order)
    - [Block name](#block-name)
    - [`endblock` name](#endblock-name)
  + [For each template variable](#for-each-template-variable)
    - [Template/context variable name](#templatecontext-variable-name)
  + [For each HTML tag](#for-each-html-tag)
    - [Empty HTML tag](#empty-html-tag)
  + [For each HTML attribute](#for-each-html-attribute)
    - [Custom attribute name](#custom-attribute-name)
    - [`class` and `id` name](#class-and-id-name)
    - [Attribute order](#attribute-order)
  + [For each CSS rule](#for-each-css-rule)
    - [Stylesheet rule order](#stylesheet-rule-order)
* [JavaScript](#javascript)
  + [For code in general](#for-code-in-general-2)
    - [String quotation marks](#string-quotation-marks-2)
  + [For each file](#for-each-file-1)
    - [Filename](#filename-2)
  + [For each function](#for-each-function)
    - [Function name](#function-name)
  + [For each variable](#for-each-variable)
    - [Variable name](#variable-name)
    - [Variable declaration (`let`/`const`/`var`)](#variable-declaration-letconstvar)

<small><i>Generated with <a href="https://ecotrust-canada.github.io/markdown-toc/">markdown-toc</a> (and manually edited).</i></small>



## Global
*Tip: [The project's `.editorconfig` file](.editorconfig) may be used to configure a text editor to format code to (roughly) fit this style guide -
especially when using an IntelliJ-based IDE, like PyCharm.*

#### Max line length
150 (can be surpassed if it's impossible to wrap).

#### Empty/blank lines
All files (including committed third-party libraries, like jQuery) should end with exactly one empty line.

There should be no more than two empty lines in a row in a file.
Exceptions to this are documentation, and markup languages (like HTML and Markdown).

#### MAKE vs. the word "make"
If writing the name of the organization (MAKE), write it in capital letters, to avoid confusion with the verb "make".



## Git

#### Branch name
Use `kebab-case`.

The type of changes that the branch will contain, can be prefixed -
with a `/` separating these parts of the branch name.
Common name prefixes include:
* `feature/` - New feature
* `bug/` - Code changes linked to a known issue
* `cleanup/` - Cleaning up or refactoring code
* `fix/` - Other fixes to the codebase

#### Commit message
Use the verb conjugation (e.g. past, present or imperative) you prefer.

The first line of the commit message should concisely outline the changes in the commit.
It should ideally be 50 characters or shorter.
<br/>*Tip: if you find yourself using the word "and" in this summary,
it's often a sign that the changes in the commit should be split into multiple commits.*

Details that were omitted from the first line should be elaborated on and explained in subsequent lines
(with an empty line between the first line, and the rest of the commit message).
These lines should comply with the same length restriction as described in [Max line length](#max-line-length).
Common things to include in this part of the commit message, are:
* A more complete overview/description/explanation of the commit's changes - especially changes that are not immediately obvious
* The reason for the changes, like if they've been discussed, or if the reason is not entirely straightforward
* Links to things like where the code came from / was inspired by, documentation, further reading, etc.
* Instructions for things that must/should be done when merging or checking out the commit
* In general, things that make up the context of the changes -
  which could potentially be useful to have in the future for understanding why it was done a certain way,
  which other changes were necessary to facilitate the changes,
  which assumptions had to be made or which special conditions made the basis for the changes, etc.



## Python

### For code in general

#### PEP8
In general, we follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
<br/>*Tip: PyCharm marks (most) PEP 8 violations with a yellow squiggly line.
Additionally, PyCharm can easily fix most of these inconsistencies - and enforce various other parts of this style guide -
using the [Reformat Code feature](https://www.jetbrains.com/pycharm/guide/tips/reformat-code/) (<kbd>Ctrl+Alt+L</kbd>/<kbd>⌥⌘L</kbd> by default) -
possibly requiring some tweaking of the settings.*

#### String quotation marks
Use `'` for "code values" that are meant to be compared exactly against some other values.
**In short: if these strings are changed, things *might* break.**
Examples include:
* Existing paths, like file paths for templates, or dotted module paths.
* Names of variables or attributes, like object attributes, keyword arguments, or template context variables.

Use `"` for messages, names, etc. that are not supposed to be compared to existing values.
**In short: if these strings are changed, nothing *should* break.**
Examples include:
* Text in a natural language, like messages that are shown to users or developers.
* Path definitions - e.g. the first argument passed to the [`path()` function](https://docs.djangoproject.com/en/stable/ref/urls/#path) -
  as these are not supposed to be directly referenced elsewhere
  (they should instead be inserted using the `reverse()` function or the `url` template tag)
  and can in principle be changed freely without altering the functionality in any way.
* Docstrings.

If unsure, or if the case in question is in a grey area, use `'`.

*[This specific coding style is loosely based on
this library's coding standards](https://docs.ckan.org/en/ckan-2.7.3/contributing/python.html#use-single-quotes).*

#### Quotation marks inside strings
Prefer using the proper Unicode characters for quotation marks in the language of the string in question
(e.g. `“` and `”` in English, and `«` and `»` in Norwegian).

Avoid using the `"` (or `\"`) character inside translated strings.
Instead, use the Unicode characters mentioned above, or HTML character entities like `&quot;`.

#### String concatenation
Prefer using [f-strings](https://www.python.org/dev/peps/pep-0498/) for string concatenation;
if an f-string is hard to read, extract inserted code to variables, and insert the variables instead.

For translation strings (using `gettext` or `gettext_lazy`), use the standard `format()` method for concatenation.
For example:<br/>`_("{chant} Batman!").format(chant="NaN" * 15)` (where `gettext_lazy` is imported as `_`).

#### Trailing commas
Always leave a trailing comma after the last element in a wrapped list/tuple/set/dictionary initialization expression
or wrapped function/constructor call.

#### Operator wrapping
When wrapping an expression containing operators (like `+`, `&` and `and`),
place the operators first on each wrapped line (instead of last on the previous lines).
This also applies to similar things, like list comprehension expressions and conditional expressions (aka ternary operator).

To illustrate, a good example of wrapping the following code:
```python
def func(long_condition_expr, other_long_expr, list_of_lists):
    if long_condition_expr and long_condition_expr:
        return other_long_expr + other_long_expr
    return [element for inner_list in list_of_lists for element in inner_list if element is not None]
```
can be:
```python
def func(long_condition_expr, other_long_expr, list_of_lists):
    if (long_condition_expr
            and long_condition_expr):
        return (
                other_long_expr
                + other_long_expr
        )
    return [
        element
        for inner_list in list_of_lists
        for element in inner_list
        if element is not None
    ]
```

#### Imports
Group imports in three "paragraphs" (separated by an empty line) in the following order:
1. Modules from Python's standard library
2. Third-party modules
3. Modules part of this project

Within each import group/paragraph, sort plain imports first, followed by `from` imports.
Additionally, sort imports alphabetically, including names listed in `from` imports.
<br/>*Tip: All of this can easily be done using PyCharm's
[Optimize Imports feature](https://www.jetbrains.com/pycharm/guide/tips/optimize-imports/) (<kbd>Ctrl+Alt+O</kbd>/<kbd>⌃⌥O</kbd> by default) -
possibly requiring some tweaking of the settings.*

All imports in a file that are from the same app as the mentioned file, should be relative
(e.g. `from .models import User` or `from .. import views`).


### For each module (file)

#### Empty/blank lines
Leave two empty lines between class and function (i.e. not method) definitions, and after all the imports in a module.

#### Folder/directory location
* Tests should be placed within a `tests` directory per app.
* Templates should be placed within an `<app name>` directory, within a `templates` directory per app.
  * For example:
    * `app_name/templates/app_name/template_name.html`
* [Static files](https://docs.djangoproject.com/en/stable/howto/static-files/) (like CSS, JavaScript or image files)
  should be placed within a directory named after the file type/category, within an `<app name>` directory, within a `static` directory per app.
  * For example:
    * `app_name/static/app_name/css/stylesheet.css`
    * `app_name/static/app_name/js/script.js`
    * `app_name/static/app_name/img/image.png`
* [Template tags and filters](https://docs.djangoproject.com/en/stable/howto/custom-template-tags/)
  should be placed within a `templatetags` directory per app.

#### Filename
Use `snake_case`.

Additionally:
* `modelfields.py` should be the name of files containing
  [custom *model* fields](https://docs.djangoproject.com/en/stable/howto/custom-model-fields/).
* `formfields.py` should be the name of files containing
  [custom *form* fields](https://docs.djangoproject.com/en/stable/ref/forms/fields/#creating-custom-fields).
* `forms.py` should be the name of files containing
  [forms](https://docs.djangoproject.com/en/stable/topics/forms/).
* `widgets.py` should be the name of files containing
  [form widgets](https://docs.djangoproject.com/en/stable/ref/forms/widgets/).
* `widgets.py` should be the name of files containing
  [form widgets](https://docs.djangoproject.com/en/stable/ref/forms/widgets/).
* `converters.py` should be the name of files containing
  [path converters](https://docs.djangoproject.com/en/stable/topics/http/urls/#registering-custom-path-converters).
* `signals.py` should be the name of files containing
  [model signals](https://docs.djangoproject.com/en/stable/topics/signals/).
* `context_processors.py` should be the name of files containing
  [template context processors](https://docs.djangoproject.com/en/stable/ref/templates/api/#writing-your-own-context-processors).
* Test modules should be named with a `test_` prefix.

###### Migration filename:
Migrations generated by Django that are named `<index>_auto_<timestamp>`, should be renamed to describe what the migration does.
<br/>*Tip: If it's difficult to summarize what the migration does with a few words,
it might be a sign that the migration should be split into multiple migrations.*

A common naming pattern is `<index>_<model name>_<field name>_<change description>`
(where `<model name>` is the lowercased model name without `_` between words),
but **making the name understandable always takes priority**.
Example names include:
* `0002_printer3dcourse_card_number`
  * *(The field `card_number` is added to the model `Printer3DCourse`.)*
* `0009_alter_user_last_name_max_length`
  * *(The `max_length` attribute of the `last_name` field of the `User` model is altered.)*
* `0012_rename_email_to_contact_email`
  * *(The `email` field of an unspecified model is renamed to `contact_email`;
    generally, basic details like the model name should be mentioned, but if it would be confusing to read,
    and the mentioned details can be implicitly understood, they can be omitted.)*
* `0014_member_user_set_null_on_delete`
  * *(The `on_delete` attribute of the `user` field on the `Member` model is changed to `SET_NULL`.)*


### For each class

#### Class name
Use `PascalCase`.

#### Field and method order
Sort the contents of a class in the following order:
1. Constants
1. Overridden fields
1. New fields
1. Managers *(for model classes)*
    * *(E.g. `objects = <Model name>QuerySet.as_manager()`.)*
1. `Meta` class *(for model classes)*
1. Dunder (<ins>d</ins>ouble <ins>under</ins>score) methods
    * *(E.g. `__init__()` or `__str__()`.)*
1. Overridden methods
1. New methods


### For each view class

#### View class name
In general, names of views related to model objects should comply with one of the following patterns:
* `<Model name><Noun or verb>View` - in most cases;
* `Admin<Model name><Noun or verb>View` - for views that only admins should have access to;
* `API<Model name><Noun or verb>View` - for views responding with JSON;
* `AdminAPI<Model name><Noun or verb>View` - for views responding with JSON that only admins should have access to;
* where:
  * `<Model name>` is the name of the model class that the view is related to.
  * `<Noun or verb>` is a word concisely outlining the contents of the view.
    * If the view inherits from one of Django's top-level generic views (`ListView`, `DetailView`, `CreateView`, `UpdateView` or `DeleteView`),
      the word should be the name of the generic view - without the `View` suffix.

#### View class order
Sort views in the same order as they appear in the app's `urls.py` (see [Path order](#path-order)).

#### View field order
A view inheriting from one of Django's [generic views](https://docs.djangoproject.com/en/stable/ref/class-based-views/flattened-index/)
(the views that are part of the `django.views.generic` module) - and possibly also `PermissionRequiredMixin` -
should have its fields sorted in the following order:
1. `permission_required`
1. `model`
1. `queryset`
1. `form_class`/`fields`
1. `template_name`
1. `context_object_name`
1. `extra_context`
1. `success_url`


### For each function/method

#### Function/method name
Use `snake_case`.

Test methods should have a name that describes what they test and what the expected outcome is;
for example `test_event_delete_view_properly_deletes_related_objects()` (for a `DeleteView` for events)
or `test_get_related_events_returns_expected_events()` (for a model method named `get_related_events()`).


### For each URL path

#### (Endpoint) path/route
In general, try to make paths as [RESTful](https://hackernoon.com/restful-api-designing-guidelines-the-best-practices-60e1d954e7c9) as possible.

For paths that refer to views inheriting from one of the following
[generic views](https://docs.djangoproject.com/en/stable/ref/class-based-views/flattened-index/),
the path specified is encouraged:
* [`ListView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-display/#listview): `"<objects>/"`;
* [`CreateView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#createview): `"<objects>/add/"`;
* [`DetailView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-display/#detailview): `"<objects>/<pk>/"`;
* [`UpdateView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#updateview): `"<objects>/<pk>/change/"`;
* [`DeleteView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#deleteview): `"<objects>/<pk>/delete/"`;
* where:
  * `<objects>` (usually the model name) is lowercased and pluralized, without any word separator.
  * `<pk>` is a capture string for the primary key of the model - usually `<int:pk>`.

This makes the paths consistent with the ones used by the
[Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/#reversing-admin-urls),
and the names of the corresponding [default model permissions](https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions).

If a model is conceptually subordinated another model (e.g. an event occurrence model that is connected to an event model),
the paths for the views related to that "sub-model" should be relative to the paths of the "super-model" -
while still complying with the guidelines above.
For example: `event/<Event:event>/occurrences/<int:pk>/change/`
([see the docs on custom path converters](https://docs.djangoproject.com/en/stable/topics/http/urls/#registering-custom-path-converters)).

Lastly, let all paths end with a `/`
(except if the first argument to `path()` would have been `"/"`, in which case it should be an empty string).

#### Path name
Use `snake_case`.

In general, paths should have the same name as the view they refer to (see [View class name](#view-class-name)),
but `snake_case`d and without the `View` suffix.

#### Path order
In general, sort paths based on the following order:
1. `""`
1. `"<objects>/"`
1. `"<objects>/add/"`
1. `"<objects>/<pk>/"`
1. `"<objects>/<pk>/change/"`
1. `"<objects>/<pk>/delete/"`
1. `"<objects>/<pk>/<other paths>"`
1. `"<other objects>/"`

#### `urlpatterns` organization
In general, place paths with a common prefix inside separate lists,
that are then [`include()`d](https://docs.djangoproject.com/en/stable/ref/urls/#include) with the mentioned prefix.

To illustrate, a good example of reorganizing the following paths:
```python
from django.urls import path


urlpatterns = [
    path("events/", ..., name='event_list'),
    path("events/add/", ..., name='event_create'),
    path("events/<Event:event>/", ..., name='event_detail'),
    path("events/<Event:event>/change/", ..., name='event_update'),
    path("events/<Event:event>/occurrences/", ..., name='event_occurrence_list'),
    path("events/<Event:event>/occurrences/<int:pk>/", ..., name='event_occurrence_detail'),
]
```
would be:
```python
from django.urls import include, path


event_occurrence_urlpatterns = [
    path("", ..., name='event_occurrence_list'),
    path("<int:pk>/", ..., name='event_occurrence_detail'),
]

specific_event_urlpatterns = [
    path("", ..., name='event_detail'),
    path("change/", ..., name='event_update'),
    path("occurrences/", include(event_occurrence_urlpatterns)),
]

event_urlpatterns = [
    path("", ..., name='event_list'),
    path("add/", ..., name='event_create'),
    path("<Event:event>/", include(specific_event_urlpatterns)),
]

urlpatterns = [
    path("events/", include(event_urlpatterns)),
]
```

###### `urlpatterns` for admin/API view paths:
For each app's `urls.py` file, place paths inside lists with the following names:
* `adminpatterns` - if they refer to a view that only admins should have access to;
* `apipatterns` - if they refer to a view responding with JSON;
* `adminapipatterns` - if they refer to a view responding with JSON that only admins should have access to.

Each of these lists should now only contain paths referring to views with the corresponding prefixes listed in [View class name](#view-class-name).

These lists should then be imported in [`web/urls.py`](web/urls.py), and `include()`d in
`admin_urlpatterns`, `api_urlpatterns` and `admin_api_urlpatterns`, respectively -
with the same path route argument as the app's other paths.
(This ensures that all paths start with the relevant `admin/`, `api/` or `api/admin/` prefix.)
For example:
```python
from django.urls import include, path

from news import urls as news_urls


admin_urlpatterns = [
    # Same path route as the other `news` app paths
    path("news/", include(news_urls.adminpatterns)),
]

admin_api_urlpatterns = [
    # Same path route as the other `news` app paths
    path("news/", include(news_urls.adminapipatterns)),
]

api_urlpatterns = [
    path("admin/", include(admin_api_urlpatterns)),
    # Same path route as the other `news` app paths
    path("news/", include(news_urls.apipatterns)),
]

urlpatterns = [
    path("admin/", include(admin_urlpatterns)),
    path("api/", include(api_urlpatterns)),
    # The `news` app's base path route argument ("news/")
    path("news/", include('news.urls')),
]
```


### For each variable/field

#### Variable/field name
Use `snake_case`.

An exception to this is when the variable value is a reference to a specific model class -
in which case, the variable should have the same name as the model it references;
for example: `InheritanceGroup = apps.get_model('groups', 'InheritanceGroup')`.

#### Model field definition arguments
Pass all arguments as keyword arguments.

Wrap all keyword arguments of relation fields (`ForeignKey`, `OneToOneField` and `ManyToManyField`) - i.e. place them on separate lines.

###### Model field keyword argument order:
Sort the keyword arguments in the following order:
1. `to`
1. `on_delete`
1. `null`
1. `blank`
1. `choices`
1. `max_length`
1. `default`
1. Other keyword arguments
1. `validators`
1. `related_name`
1. `verbose_name`
1. `help_text`

###### Model field argument value:
* `verbose_name`s should start with a lowercase letter, except if it's a name (like MAKE or GitHub).
  * [See the docs for a description of this convention](https://docs.djangoproject.com/en/stable/topics/db/models/#verbose-field-names)
    (specifically at the end of the linked section).
  * If this name is used somewhere it's not automatically uppercased,
    use the [`capfirst` template filter](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#capfirst)
    (or `django.utils.text.capfirst` for Python code) where the name is inserted.



## Django templates / HTML / CSS

### For code in general

#### String quotation marks
Use `"` for everything pure HTML and CSS.

Inside template tags and filters, use [the same quotation marks as for Python](#string-quotation-marks).
Examples include:
* `'` for:
  * `url` names
  * `extends`, `include` and `static` paths
* `"` for:
  * `translate`/`trans` strings

#### Hex (color) code literals
Use uppercase `A`-`F`, to make them look more similar to the other digits.


### For each file

#### Empty/blank lines
Leave two empty lines after all the `extends` and `load` template tags in a template.

#### Filename
Use `snake_case`.

###### Django template filenames:
In general, templates referred to by the `template_name` field of a view, should have the same name as that view
(see [View class name](#view-class-name)), but `snake_case`d and without the `View` suffix.
An exception to this is if the view inherits from `CreateView` or `UpdateView`,
in which case the `<Noun or verb>` in the [view class name patterns](#view-class-name) should be `form` in the template name.

###### CSS filenames:
If a `.css` file is the "main" stylesheet for a specific template, it should have the same name as the template.


### For each template block

#### Block order
Sort the blocks in a child template in the same order as they appear in the parent template(s).

#### Block name
Use `snake_case`.

#### `endblock` name
A block's name should always be repeated in the associated `endblock` template tag.


### For each template variable

#### Template/context variable name
Use `snake_case`. This also applies to variables defined using the `as` keyword or the `=` syntax.


### For each HTML tag

#### Empty HTML tag
Close empty tags with a `/>`.
For example: `<br/>` or `<input type="submit"/>`.


### For each HTML attribute

#### Custom attribute name
Use `kebab-case`, and prefix the custom attribute with [`data-`](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/data-*).
*(This enables getting or setting the attribute using jQuery's [`.data()` function](https://api.jquery.com/data/).)*

#### `class` and `id` name
Use `kebab-case`.

#### Attribute order
If present, place `id` and `class` first - in that order.


### For each CSS rule

#### Stylesheet rule order
Sort the rules in a stylesheet in (ideally) the same order as the elements they select appear in the template the stylesheet belongs to.



## JavaScript

### For code in general

#### String quotation marks
Use `"`.
This does not apply to template strings, of course.


### For each file

#### Filename
Use `snake_case`.

If a `.js` file is the "main" script for a specific template, it should have the same name as the template.


### For each function

#### Function name
Use `camelCase`.


### For each variable

#### Variable name
Use `camelCase`.

If the variable's value is a [jQuery object](https://learn.jquery.com/using-jquery-core/jquery-object/),
prefix the variable name with `$`.

#### Variable declaration (`let`/`const`/`var`)
Use:
* `const` wherever possible,
* `var` when defining or declaring variables in a template that will be used in a linked JavaScript file,
* `let` in all other cases.


------------------------------------------------------------------------------------------------------------------------------------------------------


# Code review guideline: Code smells
This list is meant as a guideline,
and only provides hints that might enhance developers' ability to notice whether some code should be changed or not;
there do exist scenarios where *not* getting rid of a code smell would be the most appropriate.

## Table of contents
* [Global](#global-1)
  + [For code in general](#for-code-in-general-3)
    - [Outdated comments](#outdated-comments)
    - [Outdated tests](#outdated-tests)
    - [Duplicated code](#duplicated-code)
    - [Magic numbers and strings](#magic-numbers-and-strings)
    - [Translations only differing in case](#translations-only-differing-in-case)
* [Python](#python-1)
  + [For code in general](#for-code-in-general-4)
    - [Unused imports](#unused-imports)
    - [Unnecessary `print` statements](#unnecessary-print-statements)
    - [Variable, function or class names shadowing built-in or imported names](#variable-function-or-class-names-shadowing-built-in-or-imported-names)
    - [Exception clause is too broad](#exception-clause-is-too-broad)
    - [Using a model object's `id` instead of `pk`](#using-a-model-objects-id-instead-of-pk)
    - [Missing prefetch of related objects](#missing-prefetch-of-related-objects)
    - [Unnecessary database queries](#unnecessary-database-queries)
  + [For each migration](#for-each-migration)
    - [`RunPython` operations missing the `reverse_code` argument](#runpython-operations-missing-the-reverse_code-argument)
  + [For each class](#for-each-class-1)
    - [Fields declared outside of the standard places](#fields-declared-outside-of-the-standard-places)
  + [For each model](#for-each-model)
    - [Creating custom model permissions that perform the same role as one of Django's default permissions](#creating-custom-model-permissions-that-perform-the-same-role-as-one-of-djangos-default-permissions)
    - [Missing `__str__()` method](#missing-__str__-method)
    - [Missing custom admin class](#missing-custom-admin-class)
    - [Making the model do validation](#making-the-model-do-validation)
  + [For each view](#for-each-view)
    - [The view is a function](#the-view-is-a-function)
    - [Improper access control (permissions)](#improper-access-control-permissions)
    - [Modifying state in `GET` requests](#modifying-state-in-get-requests)
    - [Doing input validation directly in view code](#doing-input-validation-directly-in-view-code)
    - [List view missing pagination](#list-view-missing-pagination)
    - [Missing `context_object_name`](#missing-context_object_name)
  + [For each form class](#for-each-form-class)
    - [Missing empty field check](#missing-empty-field-check)
    - [Missing error messages](#missing-error-messages)
    - [Improperly validating user input](#improperly-validating-user-input)
  + [For each test class](#for-each-test-class)
    - [Test cases not cleaning up media files](#test-cases-not-cleaning-up-media-files)
  + [For each function/method](#for-each-functionmethod-1)
    - [Mismatching overridden method signature](#mismatching-overridden-method-signature)
    - [Missing call to overridden method](#missing-call-to-overridden-method)
    - [Missing returning required data](#missing-returning-required-data)
  + [For each URL path](#for-each-url-path-1)
    - [Missing `name` argument](#missing-name-argument)
    - [Improper access control (permissions)](#improper-access-control-permissions-1)
  + [For each model field](#for-each-model-field)
    - [Missing `blank=True` for non-required model fields](#missing-blanktrue-for-non-required-model-fields)
    - [String-based model fields with `null=True`](#string-based-model-fields-with-nulltrue)
    - [String-based model fields with unnecessary `max_length`](#string-based-model-fields-with-unnecessary-max_length)
    - [Missing `related_name` for relation fields](#missing-related_name-for-relation-fields)
    - [Missing `verbose_name`](#missing-verbose_name)
    - [Missing appropriate constraint on field or combination of fields](#missing-appropriate-constraint-on-field-or-combination-of-fields)
* [Django templates / HTML / CSS](#django-templates--html--css-1)
  + [For code in general](#for-code-in-general-5)
    - [Lacking accessibility](#lacking-accessibility)
    - [Using a model object's `id` instead of `pk`](#using-a-model-objects-id-instead-of-pk-1)
    - [Page flow relying too much on JavaScript](#page-flow-relying-too-much-on-javascript)
    - [CSS directly in HTML](#css-directly-in-html)
  + [For each HTML tag](#for-each-html-tag-1)
    - [`<link>` or `<script>` tags in a template that's `include`d elsewhere](#link-or-script-tags-in-a-template-thats-included-elsewhere)
    - [Links missing `target="_blank"`](#links-missing-target_blank)
  + [For each HTML attribute](#for-each-html-attribute-1)
    - [Unused/unnecessary attribute](#unusedunnecessary-attribute)
    - [Unused class](#unused-class)
  + [For each CSS rule](#for-each-css-rule-1)
    - [Unused CSS rules](#unused-css-rules)
    - [Unnecessary CSS properties](#unnecessary-css-properties)
* [JavaScript](#javascript-1)
  + [For code in general](#for-code-in-general-6)
    - [JavaScript directly in HTML](#javascript-directly-in-html)
    - [Making code wait until the document is ready / window has loaded](#making-code-wait-until-the-document-is-ready--window-has-loaded)
    - [Missing semicolon](#missing-semicolon)
    - [Comparing values loosely (with `==`)](#comparing-values-loosely-with-)
    - [Unnecessary `console.log()` statements](#unnecessary-consolelog-statements)

<small><i>Generated with <a href="https://ecotrust-canada.github.io/markdown-toc/">markdown-toc</a> (and manually edited).</i></small>



## Global

### For code in general

#### Outdated comments
Comments should be kept updated and consistent with the code they're commenting on.

#### Outdated tests
Tests should be kept up-to-date and relevant to the code they test.

#### Duplicated code
Code that's commonly (accidentally) duplicated, includes:
* Code in each branch of an `if` statement
* String literals
  * *In the case of providing values for model fields' `choices` keyword argument,
    [Django's enumeration types](https://docs.djangoproject.com/en/stable/ref/models/fields/#field-choices-enum-types) should be used.*
* Code in templates
  * *This can (almost always) be abstracted by extracting common code to a separate template, which is then
    [included](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#include)
    or [extended](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#extends).*
* Overridden view class methods
* Initializing objects in test cases

Note that this does not apply to things that are part of a library or framework's programming style, like reversing a Django path name.

#### Magic numbers and strings
["Magic" numbers](https://en.wikipedia.org/wiki/Magic_number_(programming)) should be replaced by constants/variables.
The same applies to "magic" string literals
(e.g. a string where each character is used as a flag, or a function returning the name of a specific color).

#### Translations only differing in case
If there exists multiple translation strings with the only difference being the casing,
they should ideally be replaced by the one with the "lowest" casing, and transformed after the translation has been invoked.

For example, if both `"event"` and `"Event"` exist as translation strings,
the latter instance can be replaced by `capfirst(_("event"))` in Python code, and `{% translate "event"|capfirst %}` in template code.



## Python

### For code in general

#### Unused imports
Unused imports should be removed.

#### Unnecessary `print` statements
These should be removed,
or replaced by fitting `logging` calls - preferably through the utility functions in [`logging_utils.py`](util/logging_utils.py).

#### Variable, function or class names shadowing built-in or imported names
For example naming a parameter `int`, `filter` or `range` (shadowing built-in names),
or `date`, `time` or `path` (shadowing imported names - if they're imported in the module in question).

A common way to avoid this is by adding e.g. an `_` or `_obj` suffix, or by coming up with a different name altogether.

#### Exception clause is too broad
Having a bare `except` clause or simply catching `Exception` (or `BaseException`), should be avoided,
as the appropriate reaction to an exception in most cases depends on the specific exception type.

Catching a too broad exception can be reasonable, however,
if the caught exception is chained (using the `from` keyword) or if it's logged (in which case the exception object should be included).

*[Additional reasons and tips are summed up neatly in
this article](https://consideratecode.com/2018/10/17/how-not-to-handle-an-exception-in-python/).*

#### Using a model object's `id` instead of `pk`
The primary key field of a model can potentially be named something other than `id`,
so the `pk` property should preferably always be used.

#### Missing prefetch of related objects
When iterating through querysets and using the value of the objects' relation fields (`ForeignKey`, `OneToOneField` and `ManyToManyField`),
it's in most cases beneficial to prefetch the objects that the relation fields refer to,
so that Django doesn't have to make an additional database query for each related object that the code uses the value of
(this can naturally easily lead to considerable performance loss).
<br/>*This is, in other words, mainly relevant for views displaying multiple objects.*

This should be done by calling [`select_related()`](https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related)
and/or [`prefetch_related()`](https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related) on the queryset -
depending on the relation type of the related objects.

As an example, consider the following scenario, where the objects of two models - `Event` and `EventOccurrence` -
are listed in a template:
```python
from django.db import models


class Event(models.Model):
    pass


class EventOccurrence(models.Model):
    event = models.ForeignKey(
        to=Event,
        on_delete=models.CASCADE,
        related_name='occurrences',
    )


def get_context_data():
    # Prefetching related objects to avoid unnecessary additional database lookups
    return {
        'occurrence_objects': EventOccurrence.objects.select_related('event'),
        'event_objects': Event.objects.prefetch_related('occurrences'),
    }
```
```html
<h2>Event occurrence list</h2>
<ul>
    {% for occurrence in occurrence_objects %}
        <li>
            {{ occurrence }}
            <!-- Here, the value of the related field `event` is used -->
            - {{ occurrence.event }}
        </li>
    {% endfor %}
</ul>

<h2>Nested event occurrence list</h2>
<ul>
    {% for event in event_objects %}
        <li>{{ event }}
            <ul>
                <!-- Here, the value of the related field `occurrences` (through the `related_name` argument) is iterated through -->
                {% for occurrence in event.occurrences %}
                    <li>{{ occurrence }}</li>
                {% endfor %}
            </ul>
        </li>
    {% endfor %}
</ul>
```

#### Unnecessary database queries
Attempt to minimize the number of unnecessary database queries as much as practically possible.

The number of database queries a request triggers, can be measured by adding the following code to the Django settings file:
```python
from web.settings import LOGGING


LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
""" This would require a logging handler named `console`, which would look something like this:
'console': {
    'level': 'DEBUG',
    'filters': [...],
    'class': 'logging.StreamHandler',
}
"""
```


### For each migration

#### `RunPython` operations missing the `reverse_code` argument
Custom-written migrations with [`RunPython` operations](https://docs.djangoproject.com/en/stable/ref/migration-operations/#runpython)
should always provide the `reverse_code` argument,
so that it's possible to [unapply a migration](https://docs.djangoproject.com/en/stable/topics/migrations/#reversing-migrations).

If the `RunPython` operation doesn't need to be unapplied, or if it doesn't make sense to unapply it, one can pass
[`migrations.RunPython.noop`](https://docs.djangoproject.com/en/stable/ref/migration-operations/#django.db.migrations.operations.RunPython.noop).


### For each class

#### Fields declared outside of the standard places
All fields should be declared either at the top of the class body, or in the `__init__()` constructor -
or in the `setUp()` method of a test class.
A recommended way to declare fields that are not supposed to / don't need to have a default value,
is to use the type hint syntax - without assigning a value (i.e. just `<field name>: <field type>`).

If creating a mixin class, and it would be unwieldy to declare all the fields that are set,
one can instead add a `# noinspection PyAttributeOutsideInit` comment before the method or class definition.


### For each model

#### Creating custom model permissions that perform the same role as one of Django's default permissions
Use one (or more) of [Django's default permissions](https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions) instead.

#### Missing `__str__()` method
It's often useful to be able to see a string representation of model objects - for example when debugging.

#### Missing `get_absolute_url()` method
If there exists a detail page for a specific object,
the [`get_absolute_url()` method](https://docs.djangoproject.com/en/stable/ref/models/instances/#get-absolute-url)
should be defined and made to return the URL for that page -
preferably a URL returned by
[`django-hosts`' `reverse()` function](https://django-hosts.readthedocs.io/en/latest/reference.html#django_hosts.resolvers.reverse).


#### Missing custom admin class
It's generally useful for models to have a registered
[admin class](https://docs.djangoproject.com/en/stable/ref/contrib/admin/#modeladmin-objects),
with properly customized fields (like `list_display`, `list_filter` and `search_fields`).

#### Making the model do validation
This includes doing validation in the
[`save()` method](https://docs.djangoproject.com/en/stable/ref/models/instances/#django.db.models.Model.save),
in custom querysets' [`update()` method](https://docs.djangoproject.com/en/stable/ref/models/querysets/#django.db.models.query.QuerySet.update),
or in [model signals](https://docs.djangoproject.com/en/stable/ref/signals/#module-django.db.models.signals).

Validation should generally only be done through forms.
(This includes validators set in model fields'
[`validators` keyword argument](https://docs.djangoproject.com/en/stable/ref/models/fields/#validators) -
which are [run in model forms](https://docs.djangoproject.com/en/stable/ref/validators/#how-validators-are-run) -
and models' validation/cleaning methods -
which are [also run in model forms](https://docs.djangoproject.com/en/stable/ref/models/instances/#validating-objects).)
Constraining models' data should generally only be done through the fields' arguments (like `null` or `unique`),
or through [model constraints](https://docs.djangoproject.com/en/stable/ref/models/constraints/).

A major reason for all this, is that it's useful for developers and admins
to be able to change the state of objects to whatever they deem useful/valuable at the time -
for example through the [Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/),
or through [shell](https://docs.djangoproject.com/en/stable/ref/django-admin/#shell) -
even if it would not be valid for a user to set the same state through normal means on the website.
Another reason is that saving or updating model objects is never expected to e.g. raise a `ValidationError`.


### For each view

#### The view is a function
In almost all cases, views should be [class-based](https://docs.djangoproject.com/en/stable/topics/class-based-views/),
as this often decreases the amount of code required, and the potential for accidentally creating bugs
(by e.g. forgetting something that the class-based views implement by default), and increases the readability and reusability.

#### Improper access control (permissions)
All views that do not present a public page, should extend
[`PermissionRequiredMixin`](https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permissionrequiredmixin-mixin)
and set their `permission_required` field to one or more appropriate permissions -
or override the `has_permission()` method, for more detailed control.
Alternatively, they can extend
[`LoginRequiredMixin`](https://docs.djangoproject.com/en/stable/topics/auth/default/#the-loginrequired-mixin)
or [`UserPassesTestMixin`](https://docs.djangoproject.com/en/stable/topics/auth/default/#django.contrib.auth.mixins.UserPassesTestMixin),
if those are sufficient.

If a certain permission should only be enforced for a specific instance of a view,
the `as_view()` call can be wrapped in one of the decorators corresponding to the mixin classes mentioned above
(i.e. [`permission_required()`](https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permission-required-decorator),
[`login_required()`](https://docs.djangoproject.com/en/stable/topics/auth/default/#the-login-required-decorator),
and [`user_passes_test()`](https://docs.djangoproject.com/en/stable/topics/auth/default/#django.contrib.auth.decorators.user_passes_test)).

#### Modifying state in `GET` requests
This includes things like modifying objects in the database or files on the server.

Modifying state should be avoided to prevent things like browsers caching or prefetching the URL, or web crawlers regularly visiting the URL,
and possibly prevent [CSRF](https://owasp.org/www-community/attacks/csrf) vulnerabilities
(which would not be protected by [Django's built-in CSRF protection](https://docs.djangoproject.com/en/stable/ref/csrf/),
as that only takes effect for requests with ["unsafe" HTTP methods](https://developer.mozilla.org/en-US/docs/Glossary/Safe)).

Instead, implement the same functionality using a more proper HTTP method,
like `POST` (`CreateView`), `PUT` (`UpdateView`) or `DELETE` (`DeleteView`).

#### Doing input validation directly in view code
This should almost always be done in a form - which is automatically done in views inheriting from
[`ProcessFormView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/mixins-editing/#django.views.generic.edit.ProcessFormView),
like [`CreateView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#django.views.generic.edit.CreateView)
and [`UpdateView`](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#django.views.generic.edit.UpdateView).

#### List view missing pagination
A view presenting a list of objects that has the potential to grow very long,
should implement [pagination](https://docs.djangoproject.com/en/stable/topics/pagination/) -
both so that it's easier to navigate, and so that it won't take an impractically long time to load the page.

#### Missing `context_object_name`
`context_object_name` should be explicitly defined - with a fitting name - so that it's easier to read and write the template code.
This also implies that the default `object` and `object_list` template variables should preferably not be used.
<br/>*(Naturally, this mainly applies to views inheriting from `ListView` or `DetailView` -
or `UpdateView` if the object that's being updated is used in the template outside the form.)*


### For each form class

#### Missing empty field check
This applies especially to the [`clean()` method](https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.Form.clean),
where field values should be looked up using dictionaries' `get()` method,
and then checked for whether they're empty, before using/comparing them.
For example:
```python
from django import forms
from django.utils.translation import gettext_lazy as _


# (Extends `Form` for convenience; this should normally extend `ModelForm`)
class EventOccurrenceForm(forms.Form):
    start_time = forms.DateTimeField()
    end_time = forms.DateTimeField()

    def clean(self):
        cleaned_data = super().clean()
        # The fields won't exist in the cleaned data if they were submitted empty (even if they're both (by default) required)
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # These might be `None`
        if start_time and end_time:
            if start_time > end_time:
                error_message = _("The event cannot end before it starts.")
                code = 'invalid_relative_to_other_field'
                raise forms.ValidationError({
                    'start_time': forms.ValidationError(error_message, code=code),
                    'end_time': forms.ValidationError(error_message, code=code),
                })

        return cleaned_data
```

#### Missing error messages
When the form data is invalid in some way,
raise one or more [`ValidationError`s](https://docs.djangoproject.com/en/stable/ref/forms/validation/#raising-validationerror)
(or call [`add_error()`](https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.Form.add_error))
with an appropriate message, which should make the error understandable to the user -
including what the user can potentially do about the error (this can be implicit).

#### Improperly validating user input
Basic validation should preferably be done through validators set in the model fields'
[`validators` argument](https://docs.djangoproject.com/en/stable/ref/models/fields/#validators),
or through the model's [validation/cleaning methods](https://docs.djangoproject.com/en/stable/ref/models/instances/#validating-objects).
<br/>*(Be aware of the details and reasoning under [Making the model do validation](#making-the-model-do-validation), though.
Additionally, setting model field constraints can also be used in conjunction with the validation mentioned above, [which is detailed under
this related code smell](#missing-appropriate-constraint-on-field-or-combination-of-fields).)*

All other validation should normally be done in the form's
[`clean()` method](https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.Form.clean)
and/or `clean_<field name>()` methods (see the steps for [form and field validation](https://docs.djangoproject.com/en/stable/ref/forms/validation/)).



### For each test class

#### Test cases not cleaning up media files
When using temporary files (like [`test_utils.MOCK_JPG_FILE`](/util/test_utils.py), which is a `SimpleUploadedFile`) in tests,
these files should always be removed after the tests have run.
This can be done by simply letting the test case class extend [`test_utils.CleanUpTempFilesTestMixin`](/util/test_utils.py).



### For each function/method

#### Mismatching overridden method signature
When overriding a method, the base method signature should in most cases be directly copied - including default parameter values and type hints.
Misnamed parameters, or too few or too many parameters,
makes it more challenging to familiarize oneself with the code, and can cause hard-to-discover bugs.

An exception to this, is "catching" parameters from the base method that are not used, in standard `*args` and `**kwargs` parameters.

#### Missing call to overridden method
If required, a method should always call the base method it overrides (i.e. `super().<method name>()`).

#### Missing returning required data
If required, a method - especially overridden methods - should always return the data expected by its caller.
Examples include returning the cleaned data in a form's
[`clean()` method](https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.Form.clean)
(or [`clean_<field name>()` methods](https://docs.djangoproject.com/en/stable/ref/forms/validation/)),
or returning the created object in a form's [`save()` method](https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#the-save-method).


### For each URL path

#### Missing `name` argument
The `name` keyword argument should always be set to an appropriate and unique name
([see the docs for details on naming URL patterns](https://docs.djangoproject.com/en/stable/topics/http/urls/#naming-url-patterns)).

#### Improper access control (permissions)
*See the details of [the equivalent code smell for views](#improper-access-control-permissions);
moreover, always prefer doing access control in the views.*

If multiple related paths should all have the same permission, they can be included using the
[`decorator_include()` decorator](https://pypi.org/project/django-decorator-include/).


### For each model field

#### Missing `blank=True` for non-required model fields
Model fields that are not required to be specified when creating/updating objects (e.g. if they have `null=True`),
should have their `blank` keyword argument set to `True`,
so that [model forms](https://docs.djangoproject.com/en/stable/topics/forms/modelforms/) set their `required` attribute accordingly.

#### String-based model fields with `null=True`
*[Excerpt from the docs on the `null` option](https://docs.djangoproject.com/en/stable/ref/models/fields/#null):*
> Avoid using `null` on string-based fields such as `CharField` and `TextField`.
> If a string-based field has `null=True`, that means it has two possible values for “no data”: `NULL`, and the empty string.

#### String-based model fields with unnecessary `max_length`
The [`max_length` keyword argument](https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.CharField.max_length)
should rarely be set - unless if it would break things to not always enforce a length limit;
simply preventing users from submitting a ludicrously long string should instead be done by the forms.

An exception is for fields with the `choices` keyword argument set to a collection of strings that are all strictly of a certain length (or shorter),
where `max_length` could be set to this length.

#### Missing `related_name` for relation fields
Relation fields (`ForeignKey`, `OneToOneField` and `ManyToManyField`) should always be passed the
[`related_name` keyword argument](https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.ForeignKey.related_name) -
and it should be set to a sensible name.

#### Missing `verbose_name`
The [`verbose_name` keyword argument](https://docs.djangoproject.com/en/stable/ref/models/fields/#verbose-name)
should always be set to a translated string.

#### Missing appropriate constraint on field or combination of fields
This should ideally be done by going through each of the [model fields' options](https://docs.djangoproject.com/en/stable/ref/models/fields/)
(like `null`, `unique` or `max_length`) and considering whether they're appropriately set (or not set, if the default value is suitable),
and by reviewing the existing [model constraints](https://docs.djangoproject.com/en/stable/ref/models/constraints/)
and considering whether they're sufficient, or if some should be added.
The latter can be used to e.g. ensure the value of a field is unique per value of another field, among other things.

*(While doing this, be aware of the details and reasoning under [Making the model do validation](#making-the-model-do-validation).)*



## Django templates / HTML / CSS

### For code in general

#### Lacking accessibility
[Mozilla's accessibility testing
checklist](https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Cross_browser_testing/Accessibility#accessibility_testing_checklist)
includes a useful overview over things that can be checked that are relevant to this code smell.

To implement proper accessibility practices, Mozilla has a must-read [introductory guide on
HTML and accessibility](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML), and [a guide on
WAI-ARIA implementations](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/WAI-ARIA_basics#practical_wai-aria_implementations) -
with slightly more advanced topics, which can further improve the user experience.

Some easily accessible tools that can be used in addition to the ones mentioned in the checklist above, include
using [Firefox's Accessibility Inspector](https://developer.mozilla.org/en-US/docs/Tools/Accessibility_inspector) to check the outline of the page,
and using [Chrome's Lighthouse feature](https://developers.google.com/web/tools/lighthouse) to audit a page's technical accessibility aspects -
in addition to several other aspects of the page's quality.

Lastly, to quote Mozilla's HTML and accessibility guide mentioned above:
> The goal isn't "all or nothing"; every improvement you can make will help the cause of accessibility.

#### Using a model object's `id` instead of `pk`
*See [the equivalent code smell for Python](#using-a-model-objects-id-instead-of-pk).*

#### Page flow relying too much on JavaScript
Django excels particularly at facilitating creating static pages, and so it's generally good practice to utilize that strength,
as it will very often make the code considerably smaller (due to the large amount of generic code that is included with Django),
easier to read and maintain, and easier to link to specific states of a page (by implementing URL query parameters).
[The Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/) contains multiple good examples of this, like:
* A separate page for editing and displaying the details of a specific model object - in contrast to e.g. a modal
* Doing searching, filtering, sorting and [pagination](https://docs.djangoproject.com/en/stable/topics/pagination/) through URL query parameters
  * *These `GET` query parameters can be accessed through [the request object's `GET`
    `QueryDict`](https://docs.djangoproject.com/en/stable/ref/request-response/#querydict-objects)*
* Doing various actions (like deletion) on one or more model objects at a time using a
  [bound form](https://docs.djangoproject.com/en/stable/topics/forms/#bound-and-unbound-form-instances),
  which also shows details and consequences of completing those actions

Of course, the decision on whether to make a specific page more static or more dynamic, should be made on a case-by-case basis,
and by taking both user experience and code maintainability into consideration.

#### CSS directly in HTML
Inline CSS (in HTML tags' `style` attribute) and CSS in `<style>` tags,
should be moved to stylesheets (`.css` files) and linked with:
```html
<link rel="stylesheet" href="{% static '<!-- path -->' %}"/>
```


### For each HTML tag

#### `<link>` or `<script>` tags in a template that's `include`d elsewhere
These should be moved to the `<head>` tag of the templates that `include` this template,
so that the files linked are not potentially linked multiple times.
Furthermore, it's good practice to add a comment in the original template, saying which files should be linked when `include`-ing the template.

#### Links missing `target="_blank"`
`<a>` tags leading the user away from the "flow" of the current page, should always have its `target` attribute set to `"_blank"`.
This will make the link open in a new tab when clicked.


### For each HTML attribute

#### Unused/unnecessary attribute
These should be removed.

#### Unused class
Classes of a `class` attribute that have no effect, should be removed.


### For each CSS rule

#### Unused CSS rules
These should be removed. This includes rules selecting classes or IDs that do not exist (anymore).

#### Unnecessary CSS properties
CSS properties that have no effect, should be removed.
For example, setting the `left` property on an element that has `position: static`.



## JavaScript

### For code in general

#### JavaScript directly in HTML
JavaScript code written within `<script>` tags, should be moved to `.js` files and linked with:
```html
<script <!-- execution attribute --> src="{% static '<!-- path -->' %}"></script>
```
where `<!-- execution attribute -->` can be [`defer`](https://www.w3schools.com/tags/att_script_defer.asp)
or [`async`](https://www.w3schools.com/tags/att_script_async.asp) - if appropriate.

If the code needs some values from template variables, the values can be stored in `var` variables in a `<script>` tag -
which should also be declared at the top of the `.js` file(s) they're used in.
In that case, it's good practice to include a comment saying where the values of these variables come from.

#### Making code wait until the document is ready / window has loaded
This includes writing code within functions like `$(document).ready(function () {})` or `(function() {})()`,
and should be replaced by linking the code in a `<script>` tag with either the [`defer`](https://www.w3schools.com/tags/att_script_defer.asp)
or [`async`](https://www.w3schools.com/tags/att_script_async.asp) attribute present.

#### Missing semicolon
All statements should end with a `;`.

#### Comparing values loosely (with `==`)
The `===` operator should always be favored over `==`. [See some of the reasons in the answers to
this question](https://stackoverflow.com/questions/359494/which-equals-operator-vs-should-be-used-in-javascript-comparisons).

Of course, this also applies to `!==` vs. `!=`.

#### Unnecessary `console.log()` statements
*See [the equivalent code smell for Python](#unnecessary-print-statements).*
