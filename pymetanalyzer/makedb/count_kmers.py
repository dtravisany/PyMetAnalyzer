import subprocess
import glob
import os
import logging
import multiprocessing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging.info('Starting kmer counting')

def find_files(directory, genomes, pattern):
    """
    Finds all files within a given directory that match a certain pattern.
    
    :param directory: The directory to search within.
    :param genomes: The list of genomes to search.
    :param pattern: The pattern to match files against.
    :return: A list of file paths.
    """

    path = directory
    paths = []
    for genome in genomes:
        path = os.path.join(directory, genome)
        logging.info('Finding files in %s matching %s', path, pattern)
        paths.extend(glob.glob(os.path.join(path, pattern), recursive=True))
    return paths


def chunker(seq, size):
    """
    Splits a list into chunks of a given size.

    :param seq: The list to split.
    :param size: The size of the chunks.
    :return: A list of chunks.
    """
    logging.info('Splitting sequence into chunks of size %d', size)
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def run_jellyfish(input_file, kmer_size, hash_size, jelly_threads, output_file, gzip):
    """
    Runs the jellyfish count command on an input file and outputs a count file.
    
    :param input_file: Path to the input FASTA/Q file.
    :param output_file: Path to the output jellyfish count file.
    :param kmer_size: Size of the kmers to count.
    :param jelly_threads: Number of threads to use.
    :param hash_size: Initial hash size.
    :param gzip: Whether the input file is compressed.
    """
    logging.info('Running jellyfish on %s with k=%d, threads=%d, hash=%s', 
                 input_file, kmer_size, jelly_threads, hash_size)
    
    if gzip:
        logging.info('Input file %s is gzipped, decompressing', input_file)
        # Use zcat to decompress and then pipe to jellyfish
        zcat_cmd = ['zcat', input_file]
        jellyfish_cmd = ['jellyfish', 'count', '-m', str(kmer_size), '-s', hash_size, 
                         '-t', str(jelly_threads), '-C', '-o', output_file]

        # Open zcat subprocess
        zcat_process = subprocess.Popen(zcat_cmd, stdout=subprocess.PIPE)
        logging.info('Started zcat process %d', zcat_process.pid)
        
        # Run jellyfish command with zcat's output as input
        subprocess.run(jellyfish_cmd, stdin=zcat_process.stdout)
        zcat_process.stdout.close()  # Close the output stream
        
        logging.info('Finished running jellyfish')
    else:
        # Directly run jellyfish on uncompressed files
        logging.info('Input file %s is not compressed', input_file)
        
        command = ['jellyfish', 'count', '-m', str(kmer_size), '-s', hash_size, 
                   '-t', str(jelly_threads), '-C', '-o', output_file, input_file]
        subprocess.run(command)
        
        logging.info('Finished running jellyfish on uncompressed input')


def parallel_jellyfish_count(directory:str, genomes:list, pattern:str, kmer_sizes:range = range(2,11), hash_size:int = 1000000000, jelly_threads:int = 2, gzip:bool = True, jobs:int = 1):
    """
    Runs parallel_jellyfish_count counts k-mers in parallel across multiple FASTA files using Jellyfish.

    :param path: path to directory containing FASTA files
    :param pattern: glob pattern to match FASTA files in path
    :param genomes: list of genomes to search for files
    :param km: list of k-mer sizes to count
    :param size: Jellyfish hash size 
    :param threads: number of threads per Jellyfish job
    :param gzip: gzip compress Jellyfish output
    :param jobs: number of parallel jobs 
    """
    input_files = find_files(directory, genomes, pattern)

    tasks = [(input_file, km, hash_size, jelly_threads, f"{input_file}.{km}.jf", gzip) 
             for input_file in input_files for km in kmer_sizes]

    with multiprocessing.Pool(jobs) as pool:
        pool.starmap(run_jellyfish, tasks)


logging.info('Kmer counting completed')


