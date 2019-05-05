# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# author: Jinying Chen
# date: 2019.5.3
# ver2.0

import os
import re

cwd = os.getcwd()
local_dir=re.search(r"(^.*rankTerm_v[e]?[r]?\d+\.0)",cwd).group(1)
print ("locating resources in %s"%(local_dir))

## location of annotation file
annotation_file=local_dir+"/data/annotation/rankings_abc.tsv"
imp_terms_input_file_ls=[annotation_file]


## setting for run_mallet_lda.py
mallet_home='/home/chenj6/src/mallet-2.0.7'


## setting for extract_features.py

# resource setting
CHV_file=local_dir+"/resource/CHV/CHV_sample.tsv"
wordvec_file=local_dir+"/resource/wordvec/wordvec_sample.db"
metamap_path="/home/chenj6/src/metamap/public_mm/src/out/artifacts/main_jar/main.jar"

# feature setting
use_feat={
    "pos":1,
    "wv" :1,
    "morph":1,
    "chv":1,
    "chv_fam":1,
    "umls_type":1,
}


## setting for generate_features.py
cutoff_cnt = 2  # threshold to filter lexical features
denseWVIdx=(4,203)
# 0: tok
# 1: pos
# 2-3: morph
# 4-203 : dense wordvec

# resource setting
term_df_file=local_dir+"/resource/pittsPGN_DF.txt"
stop_words_file=local_dir+"/resource/stopwords_merged.list"
sparse_format=1  # 0 -- output all features, 1 -- only output non-zero features

topic_model_pars = [("metamap", 50), ("metamap", 100), ("metamap", 200)]

topic_model_dirs ={
    "metamap" : local_dir+"/topicM/pitts/",
    "train" : local_dir+"/topicM/output/train/",
    "test" : local_dir+"/topicM/output/test/",
}

# feature setting
use_feats = {
    'dwv': 1,
    'pos': 1,
    'lex' : 1,
    'isCHV' : 1,
    'semType' : 1,
    'CHVFam' : 1,
    'topic_m' : 1,
    'tfidf' : 1,  # tfidf, tf, idf
    'posit' : 1,  # position of first occurrence of a term
    'tlen' : 1,  # term length by # of words
    'mwlen' : 1,  # word length by # of characters of the longest word in a term
    'tlwl' : 1,  # combine tlen and wlen
}


