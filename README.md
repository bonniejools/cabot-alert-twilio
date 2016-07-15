Cabot Twilio Plugin
=====

This is the default twilio plugin package included with cabot. It contains two alert plugins (one for SMS, one for phone calls) to contact users using the Twilio API.

## Installation

If using default deployment methodology (via `fab deploy`):

Edit `conf/production.env` in your Cabot clone to include the plugin and (optionally) a version number:

    CABOT_PLUGINS_ENABLED=cabot_alert_twilio,<other plugins>

Run `fab deploy -H ubuntu@yourserver.example.com` (see [http://cabotapp.com/qs/quickstart.html](http://cabotapp.com/qs/quickstart.html) for more information).

The `CABOT_PLUGINS_ENABLED` environment variable triggers both installation of the plugin (via [Cabot's `setup.py` file](https://github.com/arachnys/cabot/blob/fc33c9859a6c249f8821c88eb8506ebcad645a50/setup.py#L6)) and inclusion in `INSTALLED_APPS`.
