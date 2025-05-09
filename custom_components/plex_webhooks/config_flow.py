from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN

class PlexWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Optionally validate input here
            return self.async_create_entry(title="Plex Webhook - " + user_input["webhook_id"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("webhook_id"): str
            }),
            errors=errors
        )
