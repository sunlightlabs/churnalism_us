from __future__ import division, print_function

from django.db import connection
from django.db.models import Count, Q
from django.core.management.base import BaseCommand
from apiproxy.models import SearchDocument, MatchedDocument, Match
from sidebyside.models import VisibleMatches, MatchCurveHistogram
from utils.batched_results import batched_results

from django.conf import settings


class Command(BaseCommand):
    help = 'Prints out a frequency table of the number of search documents by the number of matched documents.'
    args = ''

    def handle(self, *args, **options):
        matched_doc_types = [grp['matched_document__doc_type']
                             for grp in VisibleMatches.values('matched_document__doc_type').distinct()]

        unneeded_histograms = MatchCurveHistogram.objects.filter(Q(doc_type__isnull=False) & ~Q(doc_type__in=matched_doc_types))
        print(u"Deleting histograms for doctypes without any matches: {}".format(", ".join([unicode(h.doc_type) for h in unneeded_histograms])))
        unneeded_histograms.delete()

        print(u"Calculating match curve for all doctypes combined.")
        aggs = (Match.objects
                     .values('search_document')
                     .annotate(match_count=Count('pk')))
        self.create_histogram(aggs, None)

        for doc_type in matched_doc_types:
            print(u"Calculating match curve for doctype", doc_type)

            aggs = (Match.objects
                         .filter(matched_document__doc_type=doc_type)
                         .values('search_document')
                         .annotate(match_count=Count('pk')))
            self.create_histogram(aggs, doc_type)

    def create_histogram(self, aggs, doc_type):
        title = u"Number of Searches by the Number of Matching Documents"
        bin_axis_label = u"Number of documents matched."
        mass_axis_label = u"Number of unique search queries."

        default_values = {
            'title': title,
            'bin_axis_label': bin_axis_label,
            'mass_axis_label': mass_axis_label
        }
        (histo, created) = MatchCurveHistogram.objects.get_or_create(
            doc_type=doc_type,
            defaults=default_values)
        if not created:
            histo.title = title
            histo.bin_axis_label = bin_axis_label
            histo.mass_axis_label = mass_axis_label
            histo.save()
        histo.from_sequence(((grp['match_count'], 1)
                             for grp in aggs.iterator()))

