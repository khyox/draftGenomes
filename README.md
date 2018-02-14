# taxid2wgs: For any taxon, get all the NCBI WGS sequences

### Overview

NCBI WGS (Whole Genome Shotgun) is a huge database from [NCBI](https://www.ncbi.nlm.nih.gov/) including sequences from incomplete genomes that have been sequenced by a whole genome shotgun strategy. The sequences belong to hundred of thousands of different sequencing projects which should be located and downloaded individually. 

To ease the task of downloading sequences related to a NCBI taxonomical identifier (_taxid_) in any taxonomical level, here you are `taxid2wgs.py`. This script **collects sequence files from WGS projects and process them** to generate a single coherent fasta file, parsing the sequence headers to update them if needed. 

### Details

At the beginning `taxid2wgs.py` was conceived as a Python version of the [Perl script with the same name from NCBI](ftp://ftp.ncbi.nlm.nih.gov/blast/WGS_TOOLS/README_BLASTWGS.txt), but finally it now goes beyond such initial purpose.

As downloading and parsing NCBI WGS projects could take a long time (and require a lot of disk space) depending on the taxid selected, the script recovers from several errors. It has a _resume mode_ in case of any fatal interruption of the process. 

In addition, there are some other modes of operation:
   * The _reverse mode_ enables that another instance of the script could help downloading sequences without interfering with the first one, that is also parsing the sequences to generate the fasta file.
   * The _force mode_ ignores previous downloads and recreate the final FASTA file in spite of any previous run.
   * The _download mode_ for just downloading without parsing the WGS project files.
   * The _verbose mode_ substitutes the progress indicator with details about every project parsed.

It has been tested successfully in ~TB downloads with several interruptions.

### Running

`taxid2wgs.py` just requires a Python 3 interpreter. No other packages beyond the Python Standard Library ones are needed.

The output files have the format: `WGS4taxid{include}-{exclude}.fa` where `{include}` is the taxid of the root of the taxonomical subtree of interest while `{exclude}` (optional) is the taxid of the root of the excluded taxa in that subtree. Both taxids are options of the script. 

Please run `./taxid2wgs.py --help` to see all the possibilities and details.

### References

* [GenBank WGS Projects](ftp://ftp.ncbi.nih.gov/genbank/wgs/README.genbank.wgs)
* [WGS projects browser](https://www.ncbi.nlm.nih.gov/Traces/wgs/)
* [WGS projects data](ftp://ftp.ncbi.nlm.nih.gov/sra/wgs_aux/)