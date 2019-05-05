Feature Generation for EHR Notes (ver2.0)

author: Jinying Chen
=========================================
This is a python tool for generating machine learning features for ranking 
medical terms in EHR notes. The tool has been used in the following work.

Jinying Chen, Jiaping Zheng, and Hong Yu. Finding Important Terms for Patients in Their Electronic Health Records: A Learning-to-Rank Approach Using Expert Annotations. JMIR Medical Informatics (JMI). Vol. 4, No. 4:e40 (2016). PMID:27903489

=========================================


Requirements
-----------------------------------------
Python3.x is required to run the tool

Depending on where you obtained your python library, the following
packages may need to be intalled separately.
- nltk
- sqlite3

The tool uses MetaMap to identify candidate medical terms. MetaMap is 
required to run the tool. You can install MetaMap from
https://metamap.nlm.nih.gov/MainDownload.shtml

*The tool has been tested in the Linux environment with MetaMap 2014 
version and java 1.8.0_25
-----------------------------------------

 

How to use the tool
-----------------------------------------
1. put input text files in  
data/train
data/test
data/annotation

Notes:
(1) A few example notes (from http://templatelab.com/soap-note-examples/
and https://www.examples.com/business/progress-note.html) 
were provided in data/train and data/test
(2) data/annotation provided pseudo annotation for sample notes in data/train


2. obtain topic model output for the data
Notes:
(1) please run the following shell script before step 4 if using topic features
(2) please set the path variable mallet_home in bin/resource.py properly
./run_lda.sh

3. resource & feature set up
bin/resource.py

a. mallet_home=[path that installed the Mallet topic modeling tool]
 The tool can be downloaded from: http://mallet.cs.umass.edu/topics.php
b. CHV_file=[sample CHV file]
c. wordvec_file=[sample wordvec file]
d. metamap_path=[MetaMap binary]

Notes:
(1) a. is required in order to generate topic modeling features. Alternatively, 
can turn off the topic features by setting 'topic_m' to 0.
(2) b. and c. should be set properly to obtain quality features
(3) d. is required to run the tool

4. feature extraction
./run_feat_extract.sh
-----------------------------------------


Disclaimer
-----------------------------------------
THIS SOFTWARE IS PROVIDED BY THE OWNER “AS IS” AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE OWNER
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-----------------------------------------

