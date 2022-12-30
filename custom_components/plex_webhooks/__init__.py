"""Support for plex webhooks."""
import json
import logging

import requests
import voluptuous as vol

import aiohttp

from homeassistant.const import CONF_WEBHOOK_ID
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

EVENT_RECEIVED = "PLEX_EVENT"

DOMAIN = "plex_webhooks"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_WEBHOOK_ID): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    _LOGGER.debug('Got plex webhook.')
    
    data = None
    
    try:
        reader = await request.multipart()

        # Loop through multipart data
        while True:
            part = await reader.next()

            if part is None:
                break

            # Verify if part contains header
            try:
                content_type = part.headers[aiohttp.hdrs.CONTENT_TYPE]
            except KeyError:
                _LOGGER.warn('Parsed part did not contain content_type header.')
                continue
            else:
                # Verify if part is of type JSON
                if content_type == 'application/json':
                    data = await part.json()
                    _LOGGER.info('Parsed part of type JSON, stop parsing.')
                    break
                else:
                    _LOGGER.warn('Parsed part not of type JSON.')
    except:
        _LOGGER.warn('Request is not of type multipart.')
        # TODO : Return JSON
        data = await request.json()
    else:
        _LOGGER.info('Multipart request received.')
    
    # Abort if no data
    if not data:
        _LOGGER.error('No data received.')
        return None

    event = data['event']
    # We always want to set the status because if we don't then the event
    # trigger filtering doesn't work
    data['status'] = event

    playing = ['media.play', 'media.resume']
    stopped = ['media.pause', 'media.stop']
    grabbed = ['library.new']

    # 'track' is  Music
    # 'episode' is TV
    # 'movie' is Movie
    # 'clip' is Live TV
    data['type'] = data['Metadata']['type']

    if event in playing:
        _LOGGER.debug('Plex started playing')
        data['status'] = 'PLAYING'
        data['playerUuid'] = data['Player']['uuid']
    elif event in stopped:
        _LOGGER.debug('Plex stopped playing')
        data['status'] = 'STOPPED'
        data['playerUuid'] = data['Player']['uuid']
    elif event in grabbed:
        _LOGGER.debug('Plex got new media')
        data['status'] = 'GRABBED'

    hass.bus.async_fire(EVENT_RECEIVED, data)

async def async_setup(hass, config):
    _LOGGER.debug('Initing Plex Webhooks!')
    webhook_id = config[DOMAIN][CONF_WEBHOOK_ID]
    hass.components.webhook.async_register(
        DOMAIN, "Plex", webhook_id, handle_webhook
    )
    return True
