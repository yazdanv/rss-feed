# RssFeed Backend
    A backend server for rss feeds with python, FastAPI

## Run Using Docker
    docker-compose up -d

## Test Using pytest
    pytest -v

## Run server
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8007

## Update Requirements

1.  pip freeze > requirements.txt


## Formatting tools BLACK

Try black project before every commit use it like:

black path-to-dir-or-file for example => black .



## Translation

1.  Install gettext on your OS: `apt install gettext`

2.  Create folder named `locales` in your root of project. Also create these 
folder in `locales`:

    `fa` -> `LC_MESSAGES` -> `base.po` and `en` -> `LC_MESSAGES` -> `base.po`.

Now you have this hierarchy:

    `locales/fa/LC_MESSAGES/base.po` and `locales/en/LC_MESSAGES/base.po`

***Notice you need add for each lang this path, example is for en, fa***
 
3.  Find your pygettext module:

    `whereis pygettext.py` usual output is `/usr/bin/pygettext3`

4.  Find all of your messages that should be translated.
(This script find all of string that startedwith 'trans' from `utils.i18n`):

    `/usr/bin/pygettext3 -d base -o app/locales/base.pot app/`
 
5.  Copy and paste the content of the generated `base.pot` in each of `base.po` files.

or

6.  If your `base.po` file already has content, and you updated `base.pot` file,
you can merge `base.pot` into `base.po` with this command:

    `msgmerge locales/fa/LC_MESSAGES/base.po locales/base.pot -U`

7.  Now you should generate `.mo` file with this command: 

    `msgfmt -o locales/fa/LC_MESSAGES/base.mo locales/fa/LC_MESSAGES/base`

8.  Update your `config.py` file `Settings class`with these attributes:

    ```
    SUPPORTED_LANGUAGE: list = ("en", "fa")
    DEFAULT_LANGUAGE = "en"
    ```

9.  In your request to server set `Accept-Language` Header from `SUPPORTED_LANGUAGE`