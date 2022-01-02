# tgrsite
This is the repo for the Warwick Tabletop Games and Roleplaying Society website! You can find a live copy of it [here](https://www.warwicktabletop.co.uk/).

There is also a [document explaining the running of the website](https://www.warwicktabletop.co.uk/media/assets/2022/01/02/How_To_Website_Really_Good.pdf), which you can use to find out how the website is used in practice and what areas for improvement it currently has.

## How do I run a development copy of the website?
To run a local copy of the website for development, you'll need to install various bits, add the required configuration variables, and then create some bits required by Django. We'll go through each of those now.

### 1. Installing things
This step is fairly simple, particularly if you're familiar with Python projects.

1. The website is currently tested on Python 3.6. As such, you'll need to have a Python environment running that version. It is recommended that you [create a virtual environment](https://docs.djangoproject.com/en/2.0/topics/install/#installing-an-official-release-with-pip) for the app.
2. Install required Python packages using `pip install -r requirements.txt`.

### 2. Environment configuration
The website utilises a variety of environment variables. These can be set in one of two ways:

1. However you traditionally set environment variables on your system, e.g. via the `export` command in Bash. This is generally **not** recommended - it works, but the second method is preferred.
2. Create a `keys.py` and a `local_config.py` file in the same directory as `settings.py`. `keys.py` should contain one definition, `def secret()`, which just returns a secret key (see the next section). `local_config.py` can then be filled with definitions for all other variables - just write them as you'd write a usual assignment in Python (e.g. `DEBUG=False`). These two files are loaded when Django is started, so the environment will be updated accordingly.

#### Environment variables
The following environment variables are mandatory:
* `SECRET_KEY`: Site's own secret key, for encryption. See [Django's documentation of the `SECRET_KEY` setting](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-SECRET_KEY).

The following fields are optional:
* `DEBUG`: Determines whether to run the server in debug mode. See [Django's documentation of the `DEBUG` setting](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-DEBUG). DO NOT RUN A PRODUCTION SERVER WITH THIS ENABLED.
* `EMAIL_HOST`: Hostname of email API server. Email settings are required in order to properly send pasword reset emails and notifications.
* `EMAIL_HOST_USER`: Username to use to login to mail API.
* `EMAIL_HOST_PASSWORD`: Ditto, for password.
* `FROM_EMAIL`: Address to send emails from (eg "noreply@somesite.xyz").
* `HOST`: Hostname to add to allowed hosts. See [Django's documentation of the `ALLOWED_HOSTS` setting](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-ALLOWED_HOSTS).

Again, if you're using `local_config.py`, you just write these as assignments like `EMAIL_HOST=...`.

### 3. Running the website
The website needs a few more steps to set up the database and your superuser account for the first time. The following bullet points detail the steps you need to take.

* First, ensure migrations are present: `python manage.py makemigrations`
  * You may need to list all the apps, like so `python manage.py makemigrations assets exec forum gallery inventory messaging minutes navbar newsletters notifications pages redirect rpgs templatetags timetable users website_settings`
* Run database migrations: `python manage.py migrate`
* Create a super user: `python manage.py createsuperuser`
* Run the server using `python manage.py runserver` - this is how you test the website throughout development.
 * The server will be running on `localhost:8000`.
 * You should create a `Member` for your super user, since this is currently not automatically done.
  * Go to the admin site at `/admin`, log in, and add a Member object with `equiv_user` set to your superuser. IF you do not do this then your superuser will cause errors when viewing the site.
* Now you can optionally load some demo data into the database using the command `python manage.py loaddata ./tgrsite/fixture.json`. Currently, a fixture exists, but it contains data from the live website so we do not publish it to be safe. This is available on request.
* Finally, the homepage is a redirect to one of the static pages, which won't be present in the database if you've not loaded data. Create a new Page called index by going to the Admin Panel, clicking on Pages and then clicking "add new" in the top right. Name it index

## Contributing
Contributions welcome, in the form of issue submissions, pull requests, and comments.
If you want to add a feature, fork and branch the repo, and create a pull request into `master`.

If you have a great idea for a feature, please create an issue for it! Feel free to discuss issues as well within comment threads, or on the Tabletop Society Discord.