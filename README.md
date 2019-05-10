<p align="center">
<img src="https://raw.githubusercontent.com/khyox/rcf-aux/master/dGheader.png" alt="draftGenomes" width="900px"/></p><hr>
<p align="center"><b>Collect all the NCBI WGS sequences for any taxonomic subtree</b>
</p> 

____
### Overview

NCBI WGS (Whole Genome Shotgun) is a huge database from [NCBI](https://www.ncbi.nlm.nih.gov/) including sequences from incomplete genomes that have been sequenced by a whole genome shotgun strategy. Those sequences belong to hundreds of thousands of different sequencing projects which should be located and downloaded individually. 

`draftGenomes` greatly simplifies the otherwise arduous task of collecting all the NCBI WGS sequences related to a taxonomic identifier (_taxid_) at any taxonomic level. This script **downloads the appropriate sequence files from NCBI WGS projects and processes them** to generate a single coherent fasta file by parsing the sequence headers and updating them if needed. 

### Details

In the beginning, `draftGenomes` was conceived as a Python version of the [taxid2wgs Perl script from NCBI](ftp://ftp.ncbi.nlm.nih.gov/blast/WGS_TOOLS/README_BLASTWGS.txt), but finally, it now goes beyond such initial purpose.

As downloading and parsing NCBI WGS projects could take a long time (and require a lot of disk space) depending on the taxid selected, the script has progress indicators and recovers from several errors. It has a _resume mode_ in case of any fatal interruption of the process. 

In addition, there are some other modes of operation:
   * The _reverse mode_ enables another instance of the script to manage the download of sequences without interfering with the first one, which is also parsing the sequences to generate the resulting fasta file.
   * The _force mode_ ignores previous downloads and recreates the final FASTA file in spite of any previous run.
   * The _download mode_ for just downloading without parsing the WGS project files.
   * The _verbose mode_ substitutes the progress indicator with details about every project parsed.

It has been tested successfully in ~TB downloads with several forced and unforced interruptions.

### Installing

Just clone the GitHub repository or, even easier, download the script or copy&paste its source code. 

### Running

`draftGenomes` only requires a Python 3 interpreter. No other packages beyond the Python Standard Library ones are needed.

The name of the output files has the format: `WGS4taxid{include}-{exclude}.fa`, where `{include}` is the taxid of the root of the taxonomical subtree of interest, while `{exclude}` (optional) is the taxid of the root of the excluded taxa in that subtree. Both taxids are options of the script (a run with no taxid related arguments will test the script). 

Please run `./draftGenomes --help` to see all the possibilities and details.

### References

* [GenBank WGS Projects](ftp://ftp.ncbi.nih.gov/genbank/wgs/README.genbank.wgs): ftp://ftp.ncbi.nih.gov/genbank/wgs/README.genbank.wgs
* [WGS projects browser](https://www.ncbi.nlm.nih.gov/Traces/wgs/): https://www.ncbi.nlm.nih.gov/Traces/wgs/
* [WGS projects data](ftp://ftp.ncbi.nlm.nih.gov/sra/wgs_aux/): ftp://ftp.ncbi.nlm.nih.gov/sra/wgs_aux/
