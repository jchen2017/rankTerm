# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

# author: Jinying Chen
# date: 2019.5.3
# ver1.0

import os
import operator
import pickle
from subprocess import Popen, PIPE
from collections import *
import sys
import re
from resource import mallet_home

def train_LDA (input_dir, outputdir, topic_nums=[50], eval_model = 'n', num_top_words=21):   
	run="metamap"
	
	mallet_file = outputdir+"%s.mallet" % (run, )
	mallet_train_file = outputdir+"%s_train.mallet" % (run, )
	mallet_test_file = outputdir+"%s_test.mallet" % (run, )
	
	input_file = mallet_file # input file with mallet format
	
	os.chdir(mallet_home)
	
	# convert input data to mallet format 
	command = 'bin/mallet import-dir --input %s --output %s --keep-sequence --remove-stopwords --stoplist-file %s' % (input_dir, mallet_file, 'stoplists/en_plus_medical.txt') 

	print (command)
	os.system(command)

	if eval_model == 'y':
		command = 'bin/mallet split --input %s --training-file %s --testing-file %s --training-portion %s' % (mallet_file, mallet_train_file, mallet_test_file, str(0.9))
		print (command)
		os.system(command)

	eval_r = []
	for topic_num in topic_nums:
		keywords_file = outputdir+"%s_keys%i.txt" % (run, topic_num)
		comp_file = outputdir+"%s_composition%i.txt" % (run, topic_num)
		eval_output = outputdir+"%s_evalR%i" % (run, topic_num)
		model_file = outputdir+"%s_model%i" % (run, topic_num)
		word_weights_file =  outputdir+"%s_wordweights%i.txt" % (run, topic_num)
		eval_file = outputdir+"%s_eval%i.mallet" % (run, topic_num)
		infer_file = outputdir+"%s_infer%i.mallet" % (run, topic_num)    

		if eval_model == 'y':
			command = 'bin/mallet train-topics --input %s --num-topics %i --optimize-interval 10 --use-symmetric-alpha false --evaluator-filename %s --output-topic-keys %s --output-doc-topics %s --num-top-words %i' % (mallet_train_file, topic_num, eval_file, keywords_file, comp_file, num_top_words)
			print (command)
			os.system(command)

			command = 'bin/mallet evaluate-topics --input %s --output-doc-probs %s --evaluator %s' % (mallet_test_file, eval_output, eval_file)
			print (command)
			p = Popen(command, shell=True, stdout=PIPE)
			result, err = p.communicate()
			eval_r.append(result)
		
		elif eval_model == 'n':	
			command = 'bin/mallet train-topics --input %s --num-topics %i --optimize-interval 10 --use-symmetric-alpha false --output-topic-keys %s --output-doc-topics %s --num-top-words %i --output-model %s --topic-word-weights-file %s --inferencer-filename %s' % (input_file, topic_num, keywords_file, comp_file, num_top_words, model_file, word_weights_file, infer_file)	
			print (command)
			os.system(command)


	if eval_model == 'y':
		with open(output_dir+'evaluate_result.txt', 'w') as fp: 
			print >> fp, eval_r
		fp.close()


def test_LDA (input_dir, outputdir, model_dir, topic_nums):
	run="metamap"
	
	mallet_file = outputdir+"%s.mallet" % (run,)
	mallet_train_file = model_dir+"%s.mallet" % (run,)
	
	input_file = mallet_file # input file with mallet format

	os.chdir(mallet_home)
		
	# convert input data to mallet format
	command = 'bin/mallet import-dir --input %s --output %s --keep-sequence --remove-stopwords --stoplist-file %s --use-pipe-from %s' % (input_dir, mallet_file, 'stoplists/en_plus_medical.txt', mallet_train_file)

	print (command)
	os.system(command)

	for topic_num in topic_nums:
		infer_file = model_dir+"%s_infer%i.mallet" % (run, topic_num)
		doc_topic_file = outputdir+"%s_doctopic%i.txt" % (run, topic_num)

		command = 'bin/mallet infer-topics --input %s --output-doc-topics %s --inferencer %s'%(input_file, doc_topic_file, infer_file)

		print (command)
		os.system(command)


if '__main__' == __name__:
	if (len(sys.argv) < 4):
		print (sys.argv[0], "mode[train, eval, test] input_dir output_dir topic_nums [num_top_words]|[model_dir]")
		print (sys.argv[0], "train input_dir output_dir 20:30:50:100 50")
		print (sys.argv[0], "test input_dir output_dir 100 model_dir")

	else:
		mode=sys.argv[1]
		input_dir=sys.argv[2]
		output_dir=sys.argv[3]
		topic_nums=[ int(x) for x in sys.argv[4].split(":")]
		cwd = os.getcwd()

		if re.search(r"^\.\/", input_dir):
			input_dir=re.sub(r"^\.\/+", "", input_dir)	
			input_dir=cwd+"/"+input_dir

		if re.search(r"^\.\/", output_dir):
			output_dir=re.sub(r"^\.\/+", "", output_dir)
			output_dir=cwd+"/"+output_dir
	
		if mode in ["train", "eval"]:
			num_top_words=int(sys.argv[5])+1
			eval_model="n"

			if mode == "eval":
				eval_model="y"
			train_LDA (input_dir, output_dir, topic_nums, eval_model, num_top_words)

		elif mode == "test":
			model_dir=sys.argv[5]
			if re.search(r"^\.\/", model_dir):
				model_dir=re.sub(r"^\.\/+", "", model_dir)	
				model_dir=cwd+"/"+model_dir
				print (input_dir, output_dir, model_dir)
			
			test_LDA (input_dir, output_dir, model_dir, topic_nums)

