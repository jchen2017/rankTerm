#!/bin/sh

workdir=.

logdir=./logfiles/

model_dir=$workdir/topicM/pitts/
input_dir=$workdir/data/
output_dir=$workdir/topicM/output/
mkdir -p $logdir $output_dir

for dataset in train test
do
    mkdir -p $output_dir/$dataset
    input_dir2=$input_dir/$dataset/
    output_dir2=$output_dir/$dataset/
    echo "python bin/run_mallet_ldaR.py test $input_dir2 $output_dir2 50:100:200 $model_dir > $logdir/topicM_${dataset}.log"
    python bin/run_mallet_lda.py test $input_dir2 $output_dir2 50:100:200 $model_dir > $logdir/topicM_${dataset}.log
done
