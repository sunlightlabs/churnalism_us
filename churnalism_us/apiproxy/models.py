# -*- coding: utf-8 -*-

import re
import logging
from hashlib import sha1
from uuid import uuid4, uuid5, NAMESPACE_URL
from datetime import datetime
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

    # uuid is derived from url generated randomly in .save()
    uuid = models.CharField(max_length=32,
                            null=False,
                            blank=False,
                            unique=True,
                            db_index=True)

    # hashed_url is derived from url in .save()
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

    # domain is derived from url in .save()
    domain = models.CharField(max_length=255,
                              null=True,
                              blank=False,
                              db_index=True)

    text = models.TextField(null=False,
                            blank=False)

    title = models.TextField(null=True,
                             blank=False)

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    updated = models.DateTimeField(auto_now=True,
                                   db_index=True)

    times_shared = models.IntegerField(null=True, blank=True)

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

        self.updated = datetime.now()

        super(SearchDocument, self).save()

    def __unicode__(self):
        return u'{self.uuid}, {self.title} @ {self.updated}'.format(self=self)


class IncorrectTextReport(models.Model):
    """
    Records instances of a user reporting the text for a
    SearchDocument being incorrect. We record multiple
    instances to help decide which to investigate first.
    """

    search_document = models.ForeignKey(SearchDocument,
                                        related_name='text_problems')

    problem_description = models.TextField()

    # remote_addr, user_agent, languages, and encodings all come from the
    # headers in HttpReuest.META. We save them as diagnostic information.
    remote_addr = models.CharField(max_length=15,
                                   blank=False,
                                   null=False)

    user_agent = models.TextField()

    languages = models.CharField(max_length=255)

    encodings = models.CharField(max_length=255)

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    class Meta:
        unique_together = ("search_document", "remote_addr")


class MatchedDocument(models.Model):
    """ This caches metadata about matched documents in SFM """ 
    
    doc_type = models.IntegerField(blank=False, 
                                   null=False)

    doc_id = models.IntegerField(blank=False, 
                                 null=False)

    source_url = models.TextField(blank=False, 
                                  null=False)

    source_name = models.CharField(max_length=200, 
                                   null=True, 
                                   blank=False)

   
    source_headline = models.TextField( null=True,
                                        blank=False)

    text = models.TextField(null=False,
                            blank=False)

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    updated = models.DateTimeField(auto_now=True,
                                   db_index=True)

    def __unicode__(self):
        return u'{self.doc_type: >3}, {self.doc_id: >9}, {self.source_headline} @ {self.updated}'.format(self=self)

    class Meta:
        unique_together = ("doc_type", "doc_id")


class Match(models.Model):

    search_document = models.ForeignKey(SearchDocument,
                                        db_index=True)
    
    matched_document = models.ForeignKey(MatchedDocument,
                                         db_index=True)

    overlapping_characters = models.IntegerField(null=True)

    #This is the percentage of the SearchDocument that is included in the MatchedDocument (source doc) using character overlap
    percent_churned = models.DecimalField(max_digits=5, 
                                          decimal_places=2,
                                          null=True)

    fragment_density = models.DecimalField(max_digits=5,
                                           decimal_places=2,
                                           null=True)

    #This is the number of matches between the same SearchDocument and the same MatchedDocument
    number_matches = models.IntegerField(null=False, default=0)

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    updated = models.DateTimeField(auto_now=True,
                                   db_index=True)


    confirmed = models.IntegerField(blank=True, null=True)

    response = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u'{self.search_document!s} => {self.matched_document!s}'.format(self=self)

    class Meta:
        unique_together = ('search_document', 'matched_document')

