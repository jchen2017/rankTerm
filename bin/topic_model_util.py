# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

#!/usr/bin/env python
#

import os
import sys
import re
import math
import numpy as np
import pickle

class TopicModel:
	file_mapping = ""
	p_d_t=None  # p(topic|doc)
	p_t_w=None  # p(word|topic)
	filemap={}
	modelname=""
	def __init__ (self):
		self.p_d_t={}
		self.p_t_w={}
		try:
			f=open(self.file_mapping,'r')
			line=f.readline()
			while(line):
				line=line.strip()
				matched=re.search(r'^([^\t]+),([^\t]+)\s*$',line)
				if matched != None:
					self.filemap[matched.group(1)]=matched.group(2)
			
				line=f.readline()
			f.close()	
		except:
			pass	

	def load_model_from_text (self, indir, model_name, topic_num):
		self.modelname="%s_%d"%(model_name, topic_num)
		doc_topic_dist_file=None
		word_topic_weight_file=None
		my_regex = r".*" + re.escape(model_name) + r".*" + re.escape("%d"%(topic_num))
		indir_ls=indir.split(":")
		for indir in indir_ls:
			for r,d,f in os.walk(indir):
				for file in f:
					if re.search(my_regex,file):
						if re.search(r"wordweights",file):
							word_topic_weight_file=os.path.join(r,file)
						elif re.search(r"doctopic",file):
							doc_topic_dist_file=os.path.join(r,file)
	
		# load p(topic|doc)				
		try:
			print ("load %s"%(doc_topic_dist_file))	
			f=open(doc_topic_dist_file, 'r')
		except:
			print ("fail to open",doc_topic_dist_file)
			exit (1)
			
		line=f.readline()
		while(line):
			line=line.strip()
			#matched=re.search(r'^(\d+)\t([^\t]+)\t(.*)$',line)
			matched=re.search(r'^(\d+) ([^ ]+) (.*)$',line)
			if matched != None:
				(doc_idx,file_name,d_t_string)=matched.groups()
				fname=re.search(r'^.*\/([^\/]+)\s*$',file_name).group(1)
				fname=re.sub(r'%20', ' ', fname)
				self.p_d_t[fname]={}

				#d_t_ls=d_t_string.split("\t")
				d_t_ls=d_t_string.split(" ")

				i=0
				while i < len(d_t_ls):
					topic=int(d_t_ls[i])
					prob=float(d_t_ls[i+1])
					self.p_d_t[fname][topic]=prob
					i+=2

			line=f.readline()
		f.close()

	

		# load p(word|topic)
		try:
			print ("load %s"%(word_topic_weight_file))
			f=open(word_topic_weight_file, 'r')
			line=f.readline()
			while(line):
				line=line.strip()
				matched=re.search(r'^(\d+)\t([^\t]+)\t(.*)$',line)
				if matched != None:
					(topic,word,weight)=matched.groups()
					topic=int(topic)
					weight=float(weight)
					if topic in self.p_t_w:
						self.p_t_w[topic][word]=weight
					else:
						self.p_t_w[topic]={}
						self.p_t_w[topic][word]=weight

				line=f.readline()
			f.close()

			# normalize weight L1
			for t in self.p_t_w:
				sum_w=0
				for w in self.p_t_w[t]:
					sum_w+=self.p_t_w[t][w]
				for w in self.p_t_w[t]:
					self.p_t_w[t][w]=self.p_t_w[t][w]/sum_w

		except:
			print ("fail to open",word_topic_weight_file)
			exit (1)


	# estimate p(word|doc)		
	def Prob_W_Doc (self, filename, word) :  		
		if not filename in self.p_d_t:
			try:
				filename=self.filemap[filename]
			except:
				print ("%s is not in topic model!"%(filename))
				exit (1)
		d=filename
		prob=0
		for t in self.p_d_t[d]:
			for w in self.p_t_w[t]:
				if w == word:
					prob+=self.p_t_w[t][w]*self.p_d_t[d][t]
		return prob

	# estimate p(word|doc) for a list of words
	def Prob_W_Doc_list (self, filename, wordls) :
		if not filename in self.p_d_t:
			try:
				filename=self.filemap[filename]
			except:
				print ("%s is not in topic model!"%(filename))
				for f in self.filemap:
					print (f,"\t",self.filemap[f])
				exit (1)
		d=filename
		p_dict={}
		for w in wordls:
			p_dict[w]=0

		for t in self.p_d_t[d]:
			for w in self.p_t_w[t]:
				if w in wordls:
					p_dict[w]+=self.p_t_w[t][w]*self.p_d_t[d][t]
		return p_dict


