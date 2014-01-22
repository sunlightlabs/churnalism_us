#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "USAGE: $(basename $(readlink -f $0)) bz2_file"
    exit 1
fi

if [ ! -r "$1" -o ! -f "$1" ]; then
    echo "File does not exist or is not readable: $1"
    exit 1
fi

export DJANGO_SETTINGS_MODULE=churnalism_us.settings
date_suffix=$(date +%Y%m%d%H%M)
python -m wikitools.pageprocessor \
          --continue-on-error \
          --loglevel=info \
          --log="wikipedia_load_${date_suffix}.log" \
          "$1" \
          wikipedia_scripts.storage.add_to_superfastmatch \
          wikipedia_scripts.filters.maximum_listitem_to_line_ratio[0.65] \
          wikitools.filters.minimum_text_length[1200] \
          wikitools.transforms.convert_to_plain_text \
          wikipedia_scripts.transforms.add_url_attrib \
          wikitools.filters.limit_to_format["'text/x-wiki'"] \
          wikitools.filters.drop_disambiguation_pages \
          wikitools.filters.drop_listof_pages \
          wikitools.filters.limit_to_namespace[0] \
          wikitools.filters.minimum_text_length[1200] \
          wikitools.filters.drop_redirects

