import count_kmers as ckm
import pandas as pd
"""
parallel_jellyfish_count counts k-mers in parallel across multiple FASTA files using Jellyfish.

path: path to directory containing FASTA files
pattern: glob pattern to match FASTA files in path 
km: list of k-mer sizes to count
size: Jellyfish hash size 
threads: number of threads per Jellyfish job
gzip: gzip compress Jellyfish output
jobs: number of parallel jobs 
"""

path="/mnt/biostore/proyectos/PyMetAnalyzer/pymetanalyzer/ncbi_data/genomes/ncbi_dataset/data"
pattern="*.fna.gz"
genomes=pd.read_csv("/mnt/biostore/proyectos/PyMetAnalyzer/pymetanalyzer/ncbi_data/genomes/ncbi_dataset/folders.txt")["genome"]
km=range(2,11)
ckm.parallel_jellyfish_count(path, genomes, pattern, km, "100M", 2, gzip=True, jobs=40)
