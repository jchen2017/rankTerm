# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# author: Jinying Chen
# date: 2019.5.3
# ver2.0

import os
from os import listdir
from os.path import isfile, join

import sys, getopt

import re
import math
import string
import pickle
from resource import imp_terms_input_file_ls

def normalize(term):
    #term2=re.sub(r'\s+'," ", term)
	term2=re.sub(r'\s+',"", term)
	term2=term2.strip().lower()
	return term2


def load_imp_terms_tsv (imp_term_dict,imp_terms_input_file):
	f = open(imp_terms_input_file,'r')
	line = f.readline()
	while (line):
		if re.search(r'^#',line) or (not re.search(r'^([^\t]+)\t([^\t]+)\t.*',line)):
			print ("ignore ",line)
			line = f.readline()
			continue

		line=line.rstrip()
		eles=line.split('\t')

		(fid, ann_id, term) = eles[0:3]
		fid=re.sub("\.txt", "", fid)

		#handle new format of annotation file  : fileid ann_id term
		ann_id=re.search(r"([a-cA-C])",eles[1]).group(1).lower()
		ann1="-1"
		ann2="-1"
		ann3="-1"

		if ann_id == "a":
			ann1=1
		elif ann_id == "b":
			ann2=1
		elif ann_id == "c":
			ann3=1

		term=normalize(term)

		if fid in imp_term_dict and term in imp_term_dict[fid]:
			if ann1 == "-1":
				ann1 = imp_term_dict[fid][term][0]
			if ann2 == "-1":
				ann2 = imp_term_dict[fid][term][1]
			if ann3 == "-1":
				ann3 = imp_term_dict[fid][term][2]

		try:
			imp_term_dict[fid][term]=(ann1,ann2,ann3)
		except:
			imp_term_dict[fid]={}
			imp_term_dict[fid][term]=(ann1,ann2,ann3)

		line = f.readline()

	f.close()


def label_by_term(infile, imp_term_dict, outdir, min_num_ann=1):
	(subdir,f1)=re.search(r"^.*\/([^\/]+)\/([^\/]+).txt",infile).groups()
	outfile_U=outdir+"/"+"union/"+subdir+"/"+f1+".txt"
	outfile_I=outdir+"/"+"intersect/"+subdir+"/"+f1+".txt"
	cmd="mkdir -p %s/union/%s/"%(outdir,subdir)
	os.system(cmd)
	cmd="mkdir -p %s/intersect/%s/"%(outdir,subdir)
	os.system(cmd)

	annotators={}	
	imp_terms={}

	try:	
		for t in imp_term_dict[f1]:
			imp_terms[t]={}
			anns=imp_term_dict[f1][t]
			for i in [0,1,2]:
				ann=anns[i]
				if ann != "-1":
					try:	
						annotators[i][t]=ann
					except:
						annotators[i]={}	
						annotators[i][t]=ann	
				
					imp_terms[t][i]=ann				
	except:
		print ("warning2: %s not in imp_term_dict!"%(f1))
		return 0

	if len(annotators) < min_num_ann:
		return 0	

	fout=open(outfile_U,"w")	
	f = open(infile, 'r')
	line = f.readline()
	while (line):
		if re.search(r'^##',line) or (not re.search(r'^([^\t]+)\t([^\t]+)\t.*[0-9]',line)):
			#print ("ignore ",line)
			fout.write(line)	
			line = f.readline()
			continue

		line = line.strip()
		(label,featString,add_info)=re.search(r"^([^ ]+) (.*)\t#(.*)$", line).groups()
		##print (add_info)
		(term,label2,semType,isCHV)=add_info.split("\t")
		term=normalize(term)
		label="0"

		if term in imp_terms:
			label="1"
		else:
			tlen=len(term)	
			for t in imp_terms:
				# opt 1: subsume, need to align at the end of string
				t2len=len(t)	
				if tlen > t2len and term[tlen-t2len:tlen] == t:

				# opt 2: subsume
				#if t in term:	
					print ("warning1: %s subsumes %s, positive"%(term,t)	)
					label = "1"
					break

		add_info="\t".join([term,label,semType,isCHV])		
		fout.write("%s %s\t#%s\n"%(label,featString,add_info))		
		line = f.readline()

	f.close()
	fout.close()

	if len(annotators) >= 2:
		pos_inst=0	
		fout=open(outfile_I,"w")
		f = open(infile, 'r')
		line = f.readline()
		while (line):
			if re.search(r'^##',line) or (not re.search(r'^([^\t]+)\t([^\t]+)\t.*[0-9]',line)):
				##print ("ignore ",line)
				fout.write(line)
				line = f.readline()
				continue

			line = line.strip()
			(label,featString,add_info)=re.search(r"^([^ ]+) (.*)\t#(.*)$", line).groups()
			##print (add_info)
			(term1,label2,semType,isCHV)=add_info.split("\t")
			term=normalize(term1)
			label=0
			ann_rec={}
			tlen=len(term)

			for i in annotators:
				if term in annotators[i]:
					label+=1
					ann_rec[i]=1 # 1: exact match
				else:
					for t in annotators[i]:
						t2len=len(t)
						# opt 1: subsume, need to align at the end of string 
						#if tlen > t2len and term[tlen-t2len:tlen] == t:

						# opt 2: subsume
						if t in term:
							print ("warning1: %s subsumes %s, positive"%(term,t))
							label+=1
							ann_rec[i]=2  # 2: subsume
							break
						
			
			if label > 1:			
				label = "1"
				pos_inst+=1
			
			# allow reserve subsume for one physician's annotation
			elif label == 1:
				for i in annotators:
					if i in ann_rec:
						continue	
					for t in annotators[i]:
						t2len=len(t)
						# opt 1: subsume, need to align at the end of string
						#if tlen < t2len and t[t2len-tlen:t2len] == term:

						# opt 2: subsume, relaxed
						if (term in t and len(term) > 4) or (tlen < t2len and (t[t2len-tlen:t2len] == term or t[0:tlen] == term)):
							print ("warning1.2: %s subsumes %s, positive"%(t,term))
							label+=1
							ann_rec[i]=3  # 2: reserve subsume
							break

				if label > 1:
					label = "1"
					pos_inst+=1
				else:
					label = "0"	
			else:
				label = "0"

			add_info="\t".join([term1,label,semType,isCHV])
			fout.write("%s %s\t#%s\n"%(label,featString,add_info))
			line = f.readline()

		print ("summary on %s : %d positive instances"%(outfile_I,pos_inst)	)
		f.close()
		fout.close()
	else:
		print ("%s has %d annotators!"%(infile,len(annotators)))
		
		for ann in annotators:
			for t in annotators[ann]:	
				print (ann,t)	
		
				
	return 0


if '__main__' == __name__:
	if (len(sys.argv) < 3):
		print (sys.argv[0], "inputdir outputdir")
		exit (1)
	else:
		indir=sys.argv[1]
		outdir=sys.argv[2]

		#read in important term file
		imp_term_dict={}

		for imp_terms_input_file in imp_terms_input_file_ls:
			if re.search(r'.tsv', imp_terms_input_file):
				load_imp_terms_tsv(imp_term_dict, imp_terms_input_file)
				print (imp_term_dict.keys())
			else:
				print ("annotation file %s: format not supported!"%(imp_terms_input_file))	
				
		file_ls=[]
		for r,d,f in os.walk(indir):
			for file2 in f:
				if re.search(r"featidx_map",file2):
					continue

				if re.search(r'\.txt',file2):
					infile=os.path.join(r,file2)
					file_ls.append(infile)

		for infile in file_ls:
			print ("process "+infile)
			
			label_by_term(infile, imp_term_dict, outdir, 2)

		
