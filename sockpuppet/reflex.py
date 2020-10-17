from django.template.loader import render_to_string
from django.template.backends.django import Template
from django.test import RequestFactory
from bs4 import BeautifulSoup

from .channel import Channel

PROTECTED_VARIABLES = [
    'consumer',
    'element',
    'selectors',
    'session',
    'url',
    'is_morph',
]


class Reflex:
    def __init__(
        self, consumer, url, element, selectors, identifier='', permanent_attribute_name=None
    ):
        self.consumer = consumer
        self.url = url
        self.element = element
        self.selectors = selectors
        self.session = consumer.scope['session']
        self.identifier = identifier
        self.is_morph = False
        self.permanent_attribute_name = permanent_attribute_name

    @property
    def request(self):
        factory = RequestFactory()
        request = factory.get(self.url)
        request.session = self.consumer.scope['session']
        request.user = self.consumer.scope['user']
        return request

    def get_channel_id(self):
        '''
        Override this to make the reflex send to a different channel
        other than the session_key of the user
        '''
        return self.session.session_key

    def morph(self, selectors=[], template='', data={}):
        self.is_morph = True
        if not data and not template:
            # an empty morph, nothing is sent ever.
            return

        if isinstance(template, Template):
            html = template.render(data)
        else:
            html = render_to_string(template, data)

        document = BeautifulSoup(html)
        selectors = [selector for selector in selectors if document.select(selector)]
        broadcaster = Channel(self.get_channel_id(), identifier=data['identifier'])

        for selector in selectors:
            broadcaster.morph({
                'selector': selector,
                'html': ''.join([e.decode_contents() for e in document.select(selector)]),
                'children_only': True,
                'permanent_attribute_name': self.permanent_attribute_name,
            })
        broadcaster.broadcast()
