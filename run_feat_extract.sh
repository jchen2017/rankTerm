#!/bin/sh
mkdir -p feats feats/train feats/test logfiles/

# collect feature-related information at the token level
for dataset in train test
do
    mkdir -p feats/$dataset/1 feats/$dataset/final
    python bin/extract_features.py  data/$dataset feats/$dataset/1 > logfiles/${dataset}.feat.log

done

# generate features
python bin/generate_features.py "train" feats/train/1 feats/train/final feats/train/final/featidx_map.txt >& logfiles/tok2term.train.feat.log

python bin/generate_features.py "test" feats/test/1 feats/test/final feats/train/final/featidx_map.txt >& logfiles/tok2term.test.feat.log

# label feature file by term annotation and/or cui
python bin/label_data.py feats/train/final feats/train/final_wL > logfiles/label_by_term.log
