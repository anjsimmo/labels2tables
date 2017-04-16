#!/usr/bin/env python
import labels2tables
labels = labels2tables.bib2labels("examples/sport.in.bib")
labels2tables.labels2txt(labels, "examples/sport.out.txt")
