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

import sqlite3

import sys, getopt

import re
import math
import string
import pickle
from nltk import word_tokenize, sent_tokenize, pos_tag
from resource import *


CHV_info={}

def clean(line):
	line=re.sub(r'[^\x20-\x7E]+', ' ', line)	
	line=re.sub(r'(_ ){5+}', '', line)
	line=re.sub(r'(\. +)+', '. ', line)
	line=re.sub(r'[\"\'\\\`]', '', line)
	line=re.sub(r'(^| )\.+([^ 0-9])', r'\1\2', line)
	line=re.sub(r'\*\*date\[([^\]]*)\]',r'\1 ',line)
	line=re.sub(r'\*\*name\[([^\]]*)\]','Linda ',line)
	
	return line


def output_feat (fout, feat_dict):
	sortedDict=sorted(feat_dict.items(), key=lambda x: (x[0]))
	for (idx,feat) in sortedDict:
		if "newfeat" in feat:	
			featStr=feat["oldfeat"]+feat["newfeat"]+"\t"+feat["label"]+"\t"+feat["addinfo"]+"\n"
		else:
			featStr=feat["oldfeat"]+feat["label"]+"\t"+feat["addinfo"]+"\n"
	
		fout.write(featStr)
	


def load_wv (wv_file, wv_dict):
	if not os.path.exists(wv_file):
		print ("%s does not exist!"%(wv_file))
		exit(1)

	f = open(wv_file, 'r')
	line=f.readline()
	while (line):
		line=line.rstrip()
		if re.search(r'^([^ ]+) (.*)$',line):
			(term, wv)=re.search(r'^([^ ]+) (.*)$',line).groups()

		wv_dict[term]=wv	
		line=f.readline()

	f.close()

	
def load_CHV (CHV_file, CHV_info):
	if not os.path.exists(CHV_file):
		print ("%s not exists!"%(CHV_file))
		exit (1)
	
	
	f = open(CHV_file, 'r')
	line=f.readline()
	while (line):
		line=line.rstrip()
		eles = line.split("\t")
		cui = eles[0].strip()
		term = eles[1].strip().lower()
		famScr = eles[12]

		if not term in CHV_info:
			CHV_info[term]={}
			CHV_info[term]["scrfreq"]=0
			CHV_info[term]["famScr"]=0

		if re.search(r'\\N', famScr) or famScr == "-1" :
			famScr = -1
		else:
			famScr = float(famScr)

			CHV_info[term]["scrfreq"]+=1	
			CHV_info[term]["famScr"]+=famScr

		line=f.readline()

	for term in CHV_info:
		if CHV_info[term]["scrfreq"] == 0:
			CHV_info[term]["famScr"]=-1
		else:	
			CHV_info[term]["famScr"]=1.0*CHV_info[term]["famScr"]/CHV_info[term]["scrfreq"]	

		
def extract_metamap(infile, char2tok, tok2char, metamap_dict):
	if not os.path.exists(infile):
		print ("%s not exists!"%(infile))
		exit (1)

	f = open(infile, 'r')
	sent=""
	sentid=-1
	st=0
	end=0
	mapinfo_ls=[]
	line=f.readline()
	mm_info={}
	rank_ls=[]
	p_id=0
	phrase=""

	while (line):
		line=line.rstrip()
		if re.search(r'^input text:', line):
			p_id+=1

		elif re.search('^ Id: (.*)', line):
			sentid=re.search('^ Id: .*tx\.(\d+)', line).group(1)
			sentid="p%s.%s"%(p_id, sentid)

			line=f.readline();
			sent=re.search('^ Utterance text: (.*)', line).group(1)
			line=f.readline();
			(st,stlen)=re.search('^ Position: +\((\d+),\s+(\d+)\)', line).group(1,2)
            
			mm_info[sentid]={}
			mm_info[sentid]["st"]=st
			mm_info[sentid]["stlen"]=stlen
			mm_info[sentid]['mm']=[]
			mm_info[sentid]['sent']=sent

		elif (re.search('^Phrase:', line)):
			line=f.readline().rstrip()
			phrase=re.search('^ *text:\s*(.*)$', line).group(1).strip()

		elif (re.search('^ +Score', line)):
			mapinfo={}
			mapinfo["phrase"]=phrase
			line=f.readline().rstrip()
			while(re.search('Negation Status', line) == None):
				(attr,value)=re.search('^\s*([^:]+):\s*(.*[^ ]+)$',line).group(1,2)
				
				mapinfo[attr]=value
				line=f.readline().rstrip()

			mapinfo_ls.append(mapinfo)

		elif ((re.search('^Utterance:$', line)) and (sentid != -1)):
			for mapinfo in mapinfo_ls:
				mi={}
				for attr in mapinfo.keys():
					value=mapinfo[attr]
					if (attr == "Concept Id"):
						mi["CUI"]=value
					elif (attr == "Matched Words"):
						mi["Words"]=value
					elif (attr == "Semantic Types"):
						mi["SemTYPE"]=value
					elif (re.search("Position", attr)):
						mi["Posit"]=value
					elif (attr == "phrase"):
						mi["phrase"]=value
					elif (attr == "Sources"):
						mi["src"]=value

				mm_info[sentid]['mm'].append(mi);

			sentid=-1
			sent=""
			st=0
			end=0
			mapinfo_ls=[]

		line=f.readline();

	f.close()

	if ( (re.search('^\s*$', line)) and (sentid != -1)):
		mm_info[sentid]['mm']=[]
		for mapinfo in mapinfo_ls:
			mi={}
			for attr in mapinfo.keys():
				value=mapinfo[attr]
				if (attr == "Concept Id"):
					mi["CUI"]=value
				elif (attr == "Matched Words"):
					mi["Words"]=value
				elif (attr == "Semantic Types"):
					mi["SemTYPE"]=value
				elif (re.search("Position", attr)):
					mi["Posit"]=value
				elif (attr == "phrase"):
					mi["phrase"]=value
				elif (attr == "Sources"):
					mi["src"]=value
	

			mm_info[sentid]['mm'].append(mi);

	disallowedTypes=set(["tmco"])		
	for sentid in sorted(mm_info.keys()):
		sent=mm_info[sentid]['sent']
		chars=list(sent)
		sent_st_pos=int(mm_info[sentid]['st'])
        
		for mi in mm_info[sentid]['mm']:
			cui=mi['CUI']
			semTypes=mi['SemTYPE']
			semTypes=re.sub(r'[\[\]]',r'', semTypes)
			semTypes=semTypes.split(",")
			#semOut=" ".join(semTypes)
			semOut=semTypes[0]

			isCHV=0
			if re.search(r"CHV", mi['src']):
				isCHV=1	

			if not semOut in disallowedTypes: 	
				wordStr=mi['Words'] # matched words
				wordStr=re.sub(r'[\[\]]',r'', wordStr)
				words=wordStr.split(",")
				term=" ".join(words)
				#term=re.sub(r' +',' ',term)

				positStr=mi['Posit']
				positStr=re.sub(r'[\(\[\]]',r'', positStr)
				posits=positStr.split("),")

				if len(posits) > 0 :
				#if len(posits) == 1 :
					(st_pos, str_len)=re.search(r'^(\d+),\s*(\d+)',posits[0]).groups()
					st_pos=int(st_pos)
					end_pos=st_pos+int(str_len)
					for posit in posits[1:]:
						##print (posit)
						(st_pos2, str_len2)=re.search(r'^\s*(\d+),\s*(\d+)',posit).groups()	
						st_pos2=int(st_pos2)
						if st_pos2 > st_pos:
							end_pos=st_pos2+int(str_len2)	
	
					st_pos2=st_pos-sent_st_pos
					end_pos2=end_pos-sent_st_pos					
					
					term2 = ''.join(chars[st_pos2:end_pos2])
					term2 = re.sub(r' +',' ',term2)

					
					try:
						##print (term2,st_pos,end_pos)	
						tokIdx=char2tok[st_pos]
						if not tokIdx in metamap_dict:
							metamap_dict[tokIdx]={}

						metamap_dict[tokIdx][cui]={}
						metamap_dict[tokIdx][cui]['term']=term2
						metamap_dict[tokIdx][cui]['semType']=semOut
						metamap_dict[tokIdx][cui]['firstWord']=1
						metamap_dict[tokIdx][cui]['isCHV']=isCHV

						tokIdx2=tokIdx+1
						
						while (tokIdx2 in tok2char):
							charIdx=tok2char[tokIdx2]
							if charIdx <= end_pos:
								'''	
								if not tokIdx2 in metamap_dict: 	
									metamap_dict[tokIdx2]={}
								
								metamap_dict[tokIdx2][cui]={}
								metamap_dict[tokIdx2][cui]['term']=term2
								metamap_dict[tokIdx2][cui]['semType']=semOut
								metamap_dict[tokIdx2][cui]['firstWord']=0
								metamap_dict[tokIdx2][cui]['isCHV']=isCHV
								'''
								tokIdx2+=1
							else:
								break
	
						metamap_dict[tokIdx][cui]['wordnum']=tokIdx2-tokIdx
	
					except:
						print ("warning4: mismatch between metamap output and input sentence, ignore")	
						#exit (0)


def add_umls_feat(CHV_info, outdir, feat_dict, sent):
	sentStr=" ".join(sent)
	char2tok={}
	tok2char={}
	charIdx=0
	tokIdx=0

	for tok in sent:
		char2tok[charIdx]=tokIdx
		tok2char[tokIdx]=charIdx	
		tokIdx+=1
		charIdx+=len(tok)+1

	sentStr=re.sub(r"\"", "\\\"", sentStr)
	##cmd="java -classpath /home/chenj6/src/metamap/public_mm/src/out/artifacts/main_jar/main.jar  gov.nih.nlm.nls.metamap.MetaMapApiTest -y \"%s\" > %s/temp.out"%(sentStr, outdir)
	cmd="java -classpath %s gov.nih.nlm.nls.metamap.MetaMapApiTest -y \"%s\" > %s/temp.out"%(metamap_path,sentStr,outdir)
	##print (cmd)

	os.system(cmd)

	# extract metamap output
	metamap_dict={}
	extract_metamap(outdir+"/temp.out", char2tok, tok2char, metamap_dict)

	# add UMLS/CHV feat
	idx_ls=sorted(feat_dict)
	for tokIdx in idx_ls:
		new_info=""	
		if tokIdx in metamap_dict:
			cuis=sorted(metamap_dict[tokIdx].keys())
			for cui in cuis:
				term=metamap_dict[tokIdx][cui]['term']	
				wordnum=metamap_dict[tokIdx][cui]['wordnum']
				new_info+="%s:%d:%s"%(cui,wordnum,term)
				if use_feat["umls_type"] == 1:	
					new_info+=":"+metamap_dict[tokIdx][cui]['semType']

				term2=re.sub(r' +', ' ', term.lower())
				if use_feat["chv"] == 1:
					if term2 in CHV_info:
						new_info+=":1"
					else:
						new_info+=":%d"%(metamap_dict[tokIdx][cui]['isCHV'])

				if use_feat["chv_fam"] == 1:
					chv_type=-2	
					if term2 in CHV_info:
						famScr=CHV_info[term2]['famScr']
						if famScr >= 0:
							chv_type=math.floor(famScr/0.2)
						else:
							chv_type=-1	
					new_info+=":%d,"%(chv_type)

			new_info=re.sub(r',$','',new_info)
				
	
		feat_dict[tokIdx]["addinfo"]+="\t"+new_info
		##print (tokIdx, feat_dict[tokIdx]['term'], "newinfo=%s\n"%(new_info))

	
# add metamap/CHV information
def add_umls_info (indict, outfile):
	CHV_info={}			
	if use_feat["chv"] == 1 or use_feat["chv_fam"] == 1 :			
	# load CHV information	
		load_CHV(CHV_file, CHV_info)
		

	for infile in indict:
		print ("process: "+infile)
		fout = open(outdir+"/"+infile, 'w')
		
		feat_dict={}
		sent=[]
		idx=0
		for line in indict[infile]:
			line=line.rstrip()

			if re.search(r'^##sent.*start',line):
				fout.write(line+"\n")
				continue

			if re.search(r'^##sent.*end',line):
				add_umls_feat(CHV_info, outdir, feat_dict, sent)
				#output feature for this sentence
				output_feat(fout, feat_dict)

				feat_dict={}
				sent=[]
				idx=0

				fout.write(line+"\n")
				continue

			if re.search(r'^\s*$',line):
				fout.write("\n")
				continue

			##print (line)
			(featString,addinfo)=re.search(r"^(.*)\t(#.*)$", line).groups()
			eles=featString.split("\t")
			term=eles[0]
			pos=eles[1]
			oldfeat="\t".join(eles[0:len(eles)-1])
			label=eles[len(eles)-1]
			sent.append(term)
			feat_dict[idx]={}
			feat_dict[idx]["pos"]=pos
			feat_dict[idx]["term"]=term
			feat_dict[idx]["oldfeat"]=oldfeat
			feat_dict[idx]["label"]=label
			feat_dict[idx]["newfeat"]=""
			feat_dict[idx]["addinfo"]=addinfo
			idx+=1

			###line=f.readline()


# add features extracted at token level, e.g., wordvec, morphology
def add_feat (indict, outdict):
	db=None
	cur=None
	
	if use_feat["wv"] == 1:
		# connnect to sqlite DB
		print ("connect to %s"%(wordvec_file))
		db = sqlite3.connect(wordvec_file)
		cur=db.cursor()
	

	for infile in indict:
		print ("process: "+infile)
		outfile=infile
		outdict[outfile]=[]

		for line in indict[infile]:		
			line=line.rstrip()

			if re.search(r'^\s*$',line):
				outdict[outfile].append("\n")	
				continue
			
			if re.search(r'^##sent',line):
				outdict[outfile].append(line+"\n")
				continue

			try:
				(featString,addinfo)=re.search(r"^(.*)\t(#.*)$", line).groups()
			except:
				print("illegal format of row:",line)
				exit(0)

			eles=featString.split("\t")
			term=eles[0]
			pos=eles[1]
			oldfeat="\t".join(eles[0:len(eles)-1])
			label=eles[-1]
			wv_vec=["0.0"]*200
			wv="\t".join(wv_vec)
			wc=term
			bwc=term
						
			newfeat=""
			if use_feat["morph"] == 1:
				# word class
				wc=re.sub(r'[A-Z]', "A", wc)
				wc=re.sub(r'[a-z]', "a", wc)
				wc=re.sub(r'[0-9]', "0", wc)
				wc=re.sub(r'[^A-Za-z0-9]', "x", wc)

				# brief word class
				bwc=re.sub(r'[A-Z]+', "A", wc)
				bwc=re.sub(r'[a-z]+', "a", bwc)
				bwc=re.sub(r'[0-9]+', "0", bwc)
				bwc=re.sub(r'[^A-Za-z0-9]+', "x", bwc)
				newfeat+="\t"+wc+"\t"+bwc

			term=term.lower()	
			if use_feat["wv"] == 1 :
				term=re.sub(r"\'", "''",term)
				rows = cur.execute("select * from wordvec where wrd = '{tn}'".format(tn=term))

				if rows:
					data=cur.fetchall()  # This returns all the rows from the database as a list of tuples.
					for (t,wvStr) in data:
						wvStr=wvStr.strip()
						wv=re.sub(r' +','\t',wvStr)
						break

				elif pos == "CD":
					term2 = "3"
					print ("replace %s by %s to estimate wordvec"%(term, term2))
					rows = cur.execute("select * from wordvec where wrd = %s",[term2])
					if rows:
						data=cur.fetchall()  # This returns all the rows from the database as a list of tuples.
						for (t,wvStr) in data:
							wvStr=wvStr.strip()
							wv=re.sub(r' +','\t',wvStr)
							break
				else:
					wv='\t'.join(['0.0']*200)
	
				newfeat+="\t"+wv

			outdict[outfile].append("%s%s\t%s\t%s\n"%(oldfeat,newfeat,label,addinfo))

	if db:
		db.close()


# extract tok and pos features
def extract_tok_pos (infile, outfile, outdict):
	if not os.path.exists(infile):
		print ("%s does not exist!"%(wv_file))
		exit(1)	
	else:
		f = open(infile, 'r')
		print ("process: "+infile)
		sys.stdout.flush()
		doc="".join(f.readlines())
		f.close()

		outdict[outfile]=[]
		
		# generate features
		sent_ls=sent_tokenize(doc)  #(doc.decode('utf-8'))
		tokidx=0
		sentNo=0
		for sent in sent_ls:
			if not re.search(r"^\s+$", sent):	
				sentNo+=1	
				tokens = word_tokenize(sent)
				postags = pos_tag(tokens)
				outdict[outfile].append("##sent %d : start=%d\n"%(sentNo,tokidx))
				i=0
				for (tok,pos) in postags:
					i+=1
					l="O"
					addinfo="#"
					outdict[outfile].append("%s\t%s\t%s\t%s\n"%(tok,pos,l,addinfo))
				
				tokidx+=len(tokens)
				outdict[outfile].append("##sent %d : end=%d\n"%(sentNo,tokidx))
				outdict[outfile].append("\n")


if '__main__' == __name__:
	if (len(sys.argv) < 3):
		print (sys.argv[0], "inputdir outputdir")
		exit (1)
	else:
		if use_feat["chv"] == 1 or use_feat["chv_fam"] == 1 :
			load_CHV(CHV_file, CHV_info)
	
		indir=sys.argv[1]
		outdir=sys.argv[2]
		    
		file_ls=[]
		outfile_ls=[]
		for r,d,f in os.walk(indir):
			for filename in f:
				infile=os.path.join(r,filename)
				file_ls.append(infile)
				outfile_ls.append(filename)

		f_i=0
		for infile in file_ls:
			indict={}
			outfile=outfile_ls[f_i]
			
			f_i+=1
			
			extract_tok_pos (infile, outfile, indict)

			outdict={}
			add_feat(indict, outdict)

			add_umls_info(outdict, outdir)
		
