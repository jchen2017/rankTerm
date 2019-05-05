# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

#!/usr/bin/env python
#

# author: Jinying Chen
# date: 2019.5.3
# ver2.0


import os
import sys
import re
import math
import numpy as np
import pickle
import string

from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import EnglishStemmer

import topic_model_util
from resource import *

wn_lemmatizer = WordNetLemmatizer()
stemmer=EnglishStemmer()

def normalize (term):
    term2=term.strip().lower()
    term2=re.sub(r',',"comma", term2)
    term2=re.sub(r'\s',"", term2)
    return term2

def normalize_word (word):
	word2=re.sub(r'[0-9]','',word)
	word2=word.strip(string.punctuation)
	return word2

def loadStopwords(stop_words):
	f=open(stop_words_file, 'r')
	line=f.readline()
	while (line):
		if re.search(r'^[^\t]+\t\d+$', line):
			eles=line.strip().split("\t")
			word=eles[0]
			lcword=word.lower()
			stop_words[word]=1
			stop_words[lcword]=1
		line=f.readline()
	f.close()	

				
def generate_feat(feat_dict, feats, tok_idx, tok_ls, pos_ls, wv_dict, swv_dict, term, term_len, term_posit, tok_label_ls, umls_info):
	feat_dict["st_tokidx"]=tok_idx
	feat_dict["end_tokidx"]=tok_idx + term_len
	feat_dict["term"]=term.lower()
	feat_dict["label"]=0

	(semType,isCHV,CHVfam) = umls_info
	

	if use_feats['dwv'] == 1:
		j=tok_idx
		denseWV=wv_dict[tok_ls[j]]
		j+=1
		while j < feat_dict["end_tokidx"]:
			try:	
				denseWV+=wv_dict[tok_ls[j]]	
			except:
				print ("j=",j,"tok=",tok_ls[j],"term=",term)
				#exit (1)
			j+=1

		denseWV/=term_len
		feat_dict["dwv"]=denseWV

		
	if use_feats['pos'] == 1:
		pos=pos_ls[feat_dict["end_tokidx"]-1]
		if pos == ".":
			print ("warning 2: suspicious POS feature for %s"%(term))
			pos = "DOT"
		feat_dict["pos"]=pos
		try:
			feats["pos.%s"%(pos)]+=1
		except:
			feats["pos.%s"%(pos)]=1


	if use_feats['lex'] == 1:
		words=term.split()
		#feat_dict["lex"]={}
		newwords=[]
		for word in words:
			word=normalize_word(word)
			word=stemmer.stem(word)

			if word != "":
				newwords.append(word)
	
		newterm="".join(newwords)
		feat_dict["nterm"]=newterm
		try:
			feats["nterm.%s"%newterm]+=1
		except:
			feats["nterm.%s"%newterm]=1


	if use_feats['isCHV'] == 1:
		feat_dict["isCHV"]=isCHV
		feats["isCHV.%s"%isCHV]=1

	if use_feats['semType'] == 1:
		feat_dict["semType"]=semType
		feats["semType.%s"%(semType)]=1


	if use_feats['CHVFam'] == 1:
		feat_dict["CHVFam"]=CHVfam
		feats["CHVFam.%s"%(CHVfam)]=1

	if use_feats['posit'] == 1:
		feat_dict["posit"]=term_posit
		feats["posit"]=1

	if use_feats['tlen'] == 1:
		term2=re.sub(r' [\'s\-] ','',term)
		tlen=len(term2.split())
		feat_dict["tlen"]=tlen
		feats["tlen"]=1

	if use_feats['mwlen'] == 1:
		maxwlen=0
		words=term.split()
		for w in words:
			if len(w) > maxwlen:
				maxwlen=len(w)
				
		feat_dict["mwlen"]=maxwlen
		feats["mwlen"]=1
		
	if use_feats['tlwl'] == 1:
		tl=0
		wl=0
		if 'tlen' in feats and 'mwlen' in feats:
			tl=feat_dict["tlen"]
			wl=feat_dict["mwlen"]
		else:
			wl=0
			words=term.split()
			tl=len(words)
			for w in words:
				if len(w) > wl:
					wl=len(w)


		tlwl=math.sqrt(math.log(tl+1)*math.log(wl+1))
		feat_dict["tlwl"]=tlwl
		feats["tlwl"]=1
		

def generate_feat_sent(feats, sent, tok_ls, pos_ls, tok_label_ls, posit_ls, wv_dict, swv_dict, addinfo_ls):
	# gather candidates	
	tok_idx=0	
	for addinfo in addinfo_ls:
		(dep_info,metamap_info)=addinfo.split("\t")
		##print (metamap_info)
		#####if metamap_info != "" and use_res['metamap'] == 1:
		if metamap_info != "":
			m_ners=metamap_info.split(",")
			for m_ner in m_ners:
				success=0
				#C1522577:2:follow up:hlca:1:3
				try:
					(cui,termlen,term,semtype,isCHV,CHVfam)=m_ner.split(":")
					success=1
				except:
					# if a term contains ,
					pass

				if success:
					term=re.sub(r'\s+',' ',term.lower())
					sent.append({})
					feat_dict=sent[-1]
					term_posit=posit_ls[tok_idx]
					generate_feat(feat_dict, feats, tok_idx, tok_ls, pos_ls, wv_dict, swv_dict, term, int(termlen), term_posit, tok_label_ls, (semtype,isCHV,CHVfam))
					
		tok_idx+=1
	

def generate_feat_doc(feats, doc_feat_ls, filesize_ls, infile_ls, topic_models, term_df_dict, t2t_mapping, totaldoc):
	docid=0

	for sent_ls in doc_feat_ls:
		filename=infile_ls[docid]
		filename=re.search("^.*\/([^\/]+\/[^\/]+.txt)$", filename).group(1)

		# update term position feature 
		if use_feats['posit'] == 1:
			total_tok=filesize_ls[docid]
			print ("%s has total %d toks"%(filename, total_tok))
			for sent in sent_ls:
				for feat_dict in sent:
					feat_dict['posit']=1.0*feat_dict['posit']/total_tok

		# to revise
		if use_feats['topic_m'] == 1:
			word_ls=set([])
			term2words={}
			for sent in sent_ls:
				for feat_dict in sent:
					term=feat_dict["term"]
					if not term in term2words:
						term2words[term]=set([])
						words = term.split(" ")
						for w in words:
							term2words[term].update(w.split("-"))
					word_ls.update(term2words[term])
					
			#print (word_ls)
			topic_feats=[]
			
			for topicM in topic_models:
				topic_feats.append({})
				if "/" in filename: 
					filename2=re.search(r"^.*\/([^\/]+)$", filename).group(1)
				else:
					filename2=filename
				topic_feats[-1]=topicM.Prob_W_Doc_list(filename2, word_ls)
				
					
			for sent in sent_ls:
				for feat_dict in sent:
					word_ls=term2words[feat_dict["term"]]
					i=0
					for topicM in topic_models:
						prob_dict=topic_feats[i]						
						featname=topicM.modelname
						prob=0
						for w in word_ls:
							if prob < prob_dict[w]:
								prob=prob_dict[w]
						feat_dict[featname]=prob
												
						i+=1

					
		if 	use_feats['tfidf'] == 1:
			tf_dict={}
						
			for sent in sent_ls:
				for feat_dict in sent:
					term=feat_dict["term"]
					term=normalize(term)
					if term in tf_dict:
						tf_dict[term]+=1
					else:
						tf_dict[term]=1
	
			for sent in sent_ls:
				for feat_dict in sent:
					term=feat_dict["term"]
					term=normalize(term)
					tf=tf_dict[term]
					if term in t2t_mapping:
						t=t2t_mapping[term]
						df=term_df_dict[t]
						idf=math.log(totaldoc/df)
						tfIDF=1.0*tf*idf+1
						idf+=1  # 1 is smoothing factor
					else:
						idf=1.0
						tfIDF=1.0
        
					feat_dict['tfidf']=tfIDF
					feat_dict['tf']=tf
					feat_dict['idf']=idf

		docid+=1
				

def gen_term_feature (mode, inputdir, outdir, featidx_map_file): 
	# mode : train, test

	feats={}  # keep features, used for generating feat to idx mapping
	featidx_map={}
    

	# load topic model
	topic_models=[]
	if use_feats['topic_m'] == 1:
		for (modelname, num_topic) in topic_model_pars:
			model_indir=topic_model_dirs[modelname]
			data_indir=topic_model_dirs[mode]
			topicM=topic_model_util.TopicModel()
			topicM.load_model_from_text(model_indir+":"+data_indir, modelname, num_topic)
			feats[topicM.modelname]=1
			topic_models.append(topicM)
			

	# load DF dict
	term_df_dict_orig={}		
	term_df_dict={}
	t2t_mapping={}
	totaldoc=-1
	if use_feats['tfidf'] == 1:	
		feats['tfidf'] = 1
		feats['tf'] = 1 
		feats['idf'] = 1

		f=open(term_df_file, 'rb')
		totaldoc=pickle.load(f)
		term_df_dict_orig = pickle.load(f) # not normalized
		term_df_dict = pickle.load(f) # normalized
		f.close()
		
		t2t_mapping={}
		terms=term_df_dict.keys()
		for t in terms:
			#print (t)
			t2=normalize(t)
			if t2 in t2t_mapping:
				print ("warning 1: \"%s\" (df=%d) and \"%s\" (df=%d) map to the same string!"%(t, term_df_dict[t], t2t_mapping[t2], term_df_dict[t2t_mapping[t2]]))
			else:
				t2t_mapping[t2]=t

	infile_ls=[]
	outfile_ls=[]
	for r,d,f in os.walk(indir):
		for infile in f:
			if not re.search(r"\.txt$",infile):
				continue
			infile=os.path.join(r,infile)
			infile_ls.append(infile)
			if re.search("^.*(\/[^\/]+\/[^\/]+).txt$", infile):
				#filename=re.search("^.*(\/[^\/]+\/[^\/]+.txt)$", infile).group(1)
				filename=re.search("^.*\/([^\/]+.txt)$", infile).group(1)
				outfile=outdir+"/"+filename
				outfile_ls.append(outfile)
				print ("write to ",outfile)
			else:
				print ("unkown file name format: ",infile)
				exit (1)
	


	doc_feat_ls=[]
	filesize_ls=[]

	for inputfile in infile_ls:
		f=open(inputfile, 'r')
		line=f.readline()
		doc_feat_ls.append([])
		sent_ls=doc_feat_ls[-1] # keep instances/features for this file


		print ("start processing ",inputfile)
		
		tok_position=0
		while (line) : 
			if re.search(r'^##sent.*start=', line):
				# process sentence 	
				# variable for whole dataset
				sentIdx=re.search(r'^##sent.*start=(\d+)', line).group(1)	
				print ("process sent starting from",sentIdx	)
				
				sent_ls.append([])
				sent=sent_ls[-1]

			    #variables for whole sentence
				pos_ls=[] 
				tok_ls=[]
				tok_label_ls=[]
				posit_ls=[]
				info_ls=[]
	
				wv_dict={} 
				swv_dict={} 
			
				line=f.readline()
				while (line):
					line=line.rstrip('\r\n')

					if re.search(r'^##sent.*end=', line):
						# generate features for this sentence	
						if len(tok_ls) > 0:	
							generate_feat_sent(feats, sent, tok_ls, pos_ls, tok_label_ls, posit_ls, wv_dict, swv_dict, info_ls)
							
						pos_ls=[]
						tok_ls=[]
						tok_label_ls=[]

						wv_dict={}
						swv_dict={}
					
						sent_ls.append([])
						sent=sent_ls[-1]
						break

					elif re.search(r'^\s*$', line):
						line=f.readline()
						continue
 	
					else:
						tok_position+=1
						(featString,add_info)=re.search(r"^(.*)\t#(.*)$", line).groups()	
						eles=featString.split("\t")
						tok=eles[0]
						pos=eles[1]
						label=eles[-1]
					
						posit_ls.append(tok_position)
						pos_ls.append(pos)
						tok_ls.append(tok)
						tok_label_ls.append(label)
						info_ls.append(add_info)
						
						wv_s=np.array(eles[denseWVIdx[0]:denseWVIdx[1]+1])
						wv= wv_s.astype(np.float)

						wv_dict[tok]=wv
				
						line=f.readline()
			else:						
				line=f.readline()

		filesize_ls.append(tok_position)		


	# extract doc level features
	# doc_feat_ls : a list of documents	
	generate_feat_doc(feats, doc_feat_ls, filesize_ls, infile_ls, topic_models, term_df_dict, t2t_mapping, totaldoc)

	if mode == "train" :  # generate featidx_map
		feat_idx=1
		sorted_feats=sorted(feats)
		for feat in sorted_feats:
			if not re.search(r'(pos\.)|(lex)|(nterm)',feat):
				featidx_map[feat]=feat_idx
				feat_idx+=1

		if use_feats['dwv'] == 1:
			i=denseWVIdx[0]
			j=0
			while i <= denseWVIdx[1]:
				featidx_map["dwv.%d"%(j)]=feat_idx
				feat_idx+=1
				j+=1
			
				i+=1
			
		for feat in sorted_feats:
			if re.search(r'(pos\.)|(lex)|(nterm)',feat):
				if feats[feat] > cutoff_cnt :
					featidx_map[feat]=feat_idx
					feat_idx+=1
				else:
					print ("warning 4: filter out rare feature %s (freq=%s)"%(feat,feats[feat]))
		
		print ("featidx=",feat_idx)

		pickle.dump(featidx_map, open(featidx_map_file, 'wb'))		
	
	elif mode == 'test':	
		featidx_map=pickle.load(open(featidx_map_file, 'rb'))


	sorted_feats=sorted(featidx_map.items(), key=lambda x: (x[1]))	
	print ("total ",len(sorted_feats),"feats")


	feattypeStr="###"
	for (feat,featidx) in sorted_feats:
		feattypeStr+=" %s:%s"%(featidx,feat);

	print (feattypeStr+"\n")


	stop_words={}
	loadStopwords(stop_words)

	docid=0	
	for sent_ls in doc_feat_ls:
		included_terms={}  # remove duplicate instances/terms for individual doc

		filename=infile_ls[docid]
		outputfile=outfile_ls[docid]
		fout=open(outputfile, 'w')
		fout.write(feattypeStr+"\n")

		docid+=1
		print ("doc ",docid," :",filename)

		output_feats={}
		out_idx=0
		for sent in sent_ls:
			for feat_dict in sent:
				term = feat_dict["term"]
				nterm = feat_dict["nterm"]
				label = feat_dict["label"]

				if term in stop_words:
					print ("ignore stop word: %s"%(term))
					continue

								
				ignore = 0
				if nterm in included_terms:
					ignore = 1
					if included_terms[nterm]['label'] != label:
						print ("warning 3.1: conflict label information for \"%s\" (\"%s\") vs. \"%s\", label=%s conflictlabel=%s"%(term,nterm,included_terms[nterm]['term'], label, included_terms[nterm]['label'])),
						if label > included_terms[nterm]['label'] : # "2","1" vs. "0", "2" vs. "1"
							del output_feats[included_terms[nterm]['idx']]
							ignore = 0
							print ("override")
						else:
							print ("remove")
					else:
						print ("warning 3.2: remove duplicate term  \"%s\" (\"%s\") label=%s"%(term,nterm,label))

				if ignore == 1:	
					continue	
				else:
					included_terms[nterm] = {}
					included_terms[nterm]['term']=term
					included_terms[nterm]['label']=label
					included_terms[nterm]['idx']=out_idx
						
				addinfo=term+"\t%d"%(label)+"\t"+feat_dict["semType"]+"\t"+feat_dict["isCHV"]
				#print (term,label)

				featStr="%s qid:%d"%(label, docid)
				
				for (feat,featidx) in sorted_feats:
					#if not re.search(r'\.',feat) or re.search(r'metamap.*\.\d+',feat):
					if re.search(r'^((metamap)|(tfidf)|(posit)|(idf)|(tlwl))',feat):
						val="%.6f"%(feat_dict[feat])
						'''
						if sparse_format:
							if not re.search(r'^[\.0]+$',val):
								featStr+=" %d:%s"%(featidx,val)
						else:
							featStr+=" %d:%s"%(featidx,val)
						'''
						featStr+=" %d:%s"%(featidx,val)
						continue

					elif re.search(r'^((tf)|(tlen)|(mwlen))$',feat):	
						val=feat_dict[feat]
						featStr+=" %d:%s"%(featidx,val)
						continue

					try:
						(f1,f2)=feat.split(".")
					except:
						##print ("%s (nterm=%s): l=%s, feat=%s"%(term,nterm, label,feat))
						if re.search(r'nterm\.(.*)', feat):
							f1="nterm"
							f2=re.search(r'nterm\.(.*)', feat).group(1)

						##exit (1)


					val="0"


					if re.search(r'^dwv',f1):
						val="%.6f"%(feat_dict[f1][int(f2)])
					elif re.search(r'lex', feat): 
						if f2 in feat_dict[f1]:  # lexical
							val="1"
					elif feat_dict[f1] == f2:
						val="1"

					if sparse_format:
						if not re.search(r'^[\.0]+$',val):
							featStr+=" %d:%s"%(featidx,val)
					else:
						featStr+=" %d:%s"%(featidx,val)	
				
				output_feats[out_idx]=featStr+"\t#"+addinfo+"\n"
				out_idx+=1


		out_idx_ls=sorted(output_feats.keys())
		for out_idx in out_idx_ls:
			fout.write(output_feats[out_idx])

		fout.close()
	
	return

if '__main__' == __name__:
	if (len(sys.argv) < 5):
		print (sys.argv[0], "mode inputdir outputdir featidx_map_file")
		exit (1)
	else:
		mode=sys.argv[1]	
		indir=sys.argv[2]
		outdir=sys.argv[3]
		featidx_map_file=sys.argv[4]

		gen_term_feature (mode, indir, outdir, featidx_map_file)
