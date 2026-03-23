#!/usr/bin/env python
"""
manage.py

This file is Django's command-line utility for your project.

You use it to run commands like:
- python manage.py runserver        (start the dev server)
- python manage.py makemigrations   (create migration files)
- python manage.py migrate          (apply migrations to the database)
- python manage.py createsuperuser  (create an admin user)
- python manage.py shell            (open Django shell)
"""

import os        # Lets us set/read environment variables
import sys       # Gives access to command-line arguments like runserver, migrate, etc.


def main():
    """
    The main function:
    1) Sets the settings module Django should use.
    2) Runs Django's command-line tool with whatever command you typed.
    """

    # Tell Django where your settings.py file is.
    # Because your project folder is named "config", the settings module is:
    # config/settings.py  ->  "config.settings"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        # This imports Django's command-line runner.
        # It reads settings, loads INSTALLED_APPS, connects to DB when needed, etc.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # If Django is not installed or your virtual environment is not active,
        # this error happens. We raise a helpful message.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available "
            "on your PYTHONPATH environment variable? Did you forget to activate "
            "your virtual environment?"
        ) from exc

    # This runs the command you typed in the terminal.
    # Example:
    # sys.argv might be: ["manage.py", "runserver"]
    # execute_from_command_line will run the runserver command.
    execute_from_command_line(sys.argv)


# This checks if manage.py is being run directly (not imported).
# If yes, it calls main().
if __name__ == "__main__":
    main()
