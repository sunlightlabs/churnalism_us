# -*- coding: utf-8 -*-

import re
import logging
from hashlib import sha1
from uuid import uuid4, uuid5, NAMESPACE_URL

from urlparse import urlparse
from django.db import models



class SearchDocumentManager(models.Manager):
    """
    Handles lookups for SearchDocuments. Ideally we would just
    add a unique index to the SearchDocument.url field. Unfortunately
    the Django SQL compiler is unable to generate the proper SQL for
    MySQL: https://code.djangoproject.com/ticket/2495
    Furthermore MySQL is far more efficient scanning indexes on 
    fixed-width text fields.
    """

    def lookup_by_url(self, url):
        hashtext = sha1(url).hexdigest()
        matches = self.filter(hashed_url=hashtext)
        real_matches = [m for m in matches if m.url == url]

        if len(real_matches) == 0:
            raise SearchDocument.DoesNotExist()
        elif len(real_matches) == 1:
            return matches[0]
        else:
            raise SearchDocument.MultipleObjectsReturned()


class SearchDocument(models.Model):
    """
    This stores the text of documents that have been searched for.
    """

    objects = SearchDocumentManager()

    uuid = models.CharField(max_length=32,
                            null=False,
                            blank=False,
                            unique=True,
                            db_index=True)

    hashed_url = models.CharField(max_length=40,
                                  null=False,
                                  blank=False,
                                  unique=False,
                                  db_index=True)

    url = models.TextField(max_length=4000,
                           null=False,
                           blank=False,
                           db_index=False,
                           unique=False)

    domain = models.CharField(max_length=255,
                              null=True,
                              blank=False,
                              db_index=True)

    src = models.TextField(null=False,
                           blank=False)

    text = models.TextField(null=False,
                            blank=False)

    title = models.CharField(max_length=200,
                             null=True,
                             blank=False)

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    updated = models.DateTimeField(auto_now=True,
                                   db_index=True)

    class Meta:
        ordering = ['-updated', '-created']

    def save(self):
        if not self.uuid:
            if self.url:
                self.uuid = unicode(uuid5(NAMESPACE_URL, self.url.encode('ascii', 'ignore')).get_hex())
            else:
                self.uuid = unicode(uuid4().get_hex())

        self.hashed_url = sha1(self.url).hexdigest()

        if self.url:
            (scheme, netloc, path, params, query, frag) = urlparse(self.url)
            if netloc:
                self.domain = re.sub('/:\d+$', '', netloc)

        super(SearchDocument, self).save()
