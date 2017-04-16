import os
import bibtexparser
import bibtexparser.customization
from . import tags2table as t2t
from . import table as t

def bib2labels(
    bib_file,
    keyword_filter = "",
    keyword_separator = ":",
    label_rename = {
        "ID": "reference"
    },
    fields = ["ID"]):
    """
    Extracts a labels dict suitable for table generation from a bibtex reference database
    bib_file           -- path to bibtex file
    keyword_filter     -- will skip keywords that don't begin with the keyword_filter text
    keyword_separator  -- character used to delimit hierarchical keyword
    label_rename       -- dictionary mapping old name to new name
    fields             -- additional bibtex fields to extract in addition to keywords
    output_file        -- filename of output table
    returns            -- labels dict
    """
    with open(bib_file) as bibtex_file:
        bibtex_str = bibtex_file.read()

    def customizations(record):
        # bibtexparser customizations
        # convert latex special characters (e.g. {\"a})
        record = bibtexparser.customization.convert_to_unicode(record)
        # turn keywords field into a list of keywords
        record = bibtexparser.customization.keyword(record)
        return record
    
    parser = bibtexparser.bparser.BibTexParser()
    parser.customization = customizations
    bib_database = bibtexparser.loads(bibtex_str, parser=parser)
    entries = bib_database.entries
    
    rows = []
    cols_set = set()
    
    for entry in entries:
        row = {}
        
        # Extract keywords
        keywords = entry['keyword']
        for keyword in keywords:
            if not keyword.startswith(keyword_filter):
                continue
            sub_keywords = keyword.split(keyword_separator)
            sub_keywords = [label_rename.get(k, k) for k in sub_keywords]
            if len(sub_keywords) > 1:
                head = sub_keywords[0]
                tail = sub_keywords[1:]
                row[head] = tail
                cols_set.add(head)
            else:
                row[keyword] = True
                cols_set.add(keyword)
        
        # extract extra fields
        for field in fields:
            field_rename = label_rename.get(field, field)
            row[field_rename] = entry[field]
            cols_set.add(field_rename)
        
        rows.append(row)
    
    cols = sorted(cols_set)
    
    # leave rest to inference
    lables_dict = {
        # TODO: Leave col structure to auto-inference.
        #       atomatically group mutually exculsive cols
        #       into hierarchies.
        'cols': cols,
        # TODO: Allow way to specify that source col should
        #       be sorted last (perhaps a "sort-hint" col attribute)
        # TODO: Allow types to be dict so that we can
        #       specify ref type without needing to know
        #       how many columns in advance
        #'types': {
        #    label_rename.get("ID", "ID"): "ref"
        #},
        'sort_rows': True,
        'data': rows,
    }
    
    return lables_dict

def labels2txt(
    labels,
    output_file):
    """
    Generate plaintext table
    labels      -- labels dict
    output_file -- filename of output table
    """
    table = t2t.tags2table(labels)
    presenter = t.TxtTable()
    txt = presenter.present(table)
    with open(output_file, 'w') as out:
        out.write(txt)

#def labels2tsv(
#    labels,
#    output_file):
#    """
#    Generate tab separated value table
#    labels      -- labels dict
#    output_file -- filename of output table
#    """
#    pass

#def labels2latex(
#    labels,
#    output_file,
#    output_wrapper,
#    bib_file):
#    """
#    Generate LaTeX table
#    labels         -- labels dict
#    output_file    -- filename of output LaTeX table
#    output_wrapper -- filename of output LaTeX wrapper to compile table
#    bib_file       -- bib filename for LaTeX wapper to use for citations keys
#    """
#    pass
