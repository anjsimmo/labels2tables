Labels To Tables
========================

labels2tables extracts keywords from a bibtex file, and uses them to generate an academic summary table comparing the articles.

Example
--------

Input:

::

  @article{duch_quantifying_2010,
           keywords = {game:soccer, model:network:centrality, open-access}}
  @article{yamamoto_common_2011,
           keywords = {game:soccer, model:network:scale-free, open-access}}
  @article{yaari_hot_2011,
           keywords = {game:basketball, model:sequence, open-access}}

Transformation:

::

  import labels2tables
  labels = labels2tables.bib2labels("examples/sport.in.bib")
  labels2tables.labels2txt(labels, "examples/sport.out.txt")

Output:

::

  ========================================================
  game       model       open-access reference            
  ========================================================
  soccer     network                                      
              centrality Y           duch_quantifying_2010
              scale-free Y           yamamoto_common_2011 
  basketball sequence    Y           yaari_hot_2011       
  ========================================================

Advanced
--------
The intermediate labels format encodes table data using standard Python dictionaries, lists and tuples. See `examples/*.spec.txt` for example tables, and how to describe them as a labels dictionary.

Acknowledgements
----------------
Powered by `bibtexparser`
