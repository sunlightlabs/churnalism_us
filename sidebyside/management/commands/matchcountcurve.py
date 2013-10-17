from __future__ import division, print_function

from django.db import connection
from django.db.models import Count
from django.core.management.base import BaseCommand
from apiproxy.models import SearchDocument, MatchedDocument, Match
from sidebyside.models import MatchCurveHistogram
from utils.batched_results import batched_results


class Command(BaseCommand):
    help = 'Prints out a frequency table of the number of search documents by the number of matched documents.'
    args = ''

    def handle(self, *args, **options):
        bin_axis_label = "Number of documents matched."
        mass_axis_label = "Number of unique search queries."

        for doc_type in MatchedDocument.objects.doc_types():
            print("Calculating match curve for doctype", doc_type)

            aggs = (Match.objects
                         .filter(matched_document__doc_type=doc_type)
                         .values('search_document')
                         .annotate(match_count=Count('pk')))
            
            default_values = {
                'bin_axis_label': bin_axis_label,
                'mass_axis_label': mass_axis_label
            }
            (histo, created) = MatchCurveHistogram.objects.get_or_create(
                doc_type=doc_type,
                defaults=default_values)
            histo.from_sequence(((grp['match_count'], 1)
                                 for grp in aggs.iterator()))

