#!/usr/bin/env python

# YAM SPLIT - Austin G. Davis-Richardson
# Splits barcoded, 3-paired illumina files based on a .yaml config file

import sys
import os
from glob import glob
import string

try:
    import yaml
except ImportError:
    print >> sys.stderr, "could not import yaml\ntry:\n  sudo easy_install pyyaml"
    quit(1)

# PARSE ARGUMENTS
try:
    config_file = sys.argv[1]
    reads_directory = sys.argv[2]
    output_directory = sys.argv[3]
except IndexError:
    print >> sys.stderr, "usage: %s <config.yaml> <reads_directory/> <output_directory/>" %\
        sys.argv[0]


# Parse YAML file
config = yaml.load(open(config_file))

# Make Output Directories
try:
    os.mkdir(output_directory)
except OSError:
    print >> sys.stderr, "%s exists! Delete or move." % output_directory
    quit()

for lane in config['lanes']:
    for experiment in config['lanes'][lane]:
        try:
            os.mkdir('%s/%s' % (output_directory, experiment))
        except OSError:
            continue


# DEFINE HOW FILES LOOK
FILENAME = "s_%(lane)s_%(mate)s_%(number)s_qseq.txt"
RANGE = range(1, 121) # Number goes FROM 0 TO 120

# For reverse complementing the barcode sequence
COMPLEMENT = string.maketrans('GATCRYgatcry', 'CTAGYRctagyr')

# Test reverse complement
assert 'GATCRYgatcry'.translate(COMPLEMENT) == 'CTAGYRctagyr'

# Load Barcodes
for key in config['barcodes']:
    print "%s => %s barcodes" % (key, len(config['barcodes'][key]))

# FOR LANE IN LANES
for lane in config['lanes']:
  
    print 'Lane: %s' % lane

    # FOR EXP IN LANE.EXPERIMENTS
    for experiment in config['lanes'][lane]:
        # Load BARCODES
        barcode_type = config['lanes'][lane][experiment]['barcodes']
        start, stop = config['lanes'][lane][experiment]['range'].split('-')
        start, stop = int(start), int(stop) + 1
        barcode_range = range(start, stop)
        print '\t%s (%s, %s-%s)' % (experiment, barcode_type, start, stop), 

        to_keep = dict( (v, k) for k, v in config['barcodes'][barcode_type].items() if k in barcode_range )

        # Get which lines to keep:

        kept, thrown_away = 0, 0
        for file_no in RANGE:
            line_to_barcode = {}
            filename = '%s/%s' % (reads_directory, FILENAME % {
                'lane': lane,
                'mate': 2,
                'number': '%04d' % file_no })
            
            with open(filename) as handle:
                for n, line in enumerate(handle):
                    barcode = line.split('\t')[8][::-1].translate(COMPLEMENT) 
                    if barcode in to_keep.keys():
                        line_to_barcode[n] = to_keep[barcode]
                        kept += 1
                    else:
                        thrown_away += 1

            # Output reads.
            for mate in [1, 3]:
                # MAKE HANDLES:

                handles = dict(
                    (barcode, 
                    open('%s/%s/%s' % (output_directory, experiment,
                        'IL5_L_%s_B_%03d_%s.txt' % (
                            lane, barcode, mate
                        )), 'a')) for barcode in to_keep.values()
                         
                )

                # Read Raw Reads, splitting

                infilename = '%s/%s' % (reads_directory, FILENAME % {
                    'lane': lane,
                    'mate': mate,
                    'number': '%04d' % file_no })
                
                
                with open(infilename) as handle:
                    for n, line in enumerate(handle):
                        if n in line_to_barcode:
                            barcode = line_to_barcode[n]
                            print >> handles[barcode], line.strip()


                del handles # Garbage Collector can't keep up
