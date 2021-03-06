#!/usr/bin/python

###############################################################################
# Not to spec
###############################################################################

## Import statements
import argparse
import csv
import getpass
import sys
import re
from openreview import *

## Argument handling
parser = argparse.ArgumentParser()
parser.add_argument('assignments', help="either (1) a csv file containing reviewer assignments or (2) a string of the format '<email_address>,<paper#>' e.g. 'reviewer@cs.umass.edu,23'")
parser.add_argument('--baseurl', help="base url")
parser.add_argument('--username')
parser.add_argument('--password')
args = parser.parse_args()

## Initialize the client library with username and password
if args.username!=None and args.password!=None:
    openreview = Client(baseurl=args.baseurl, username=args.username, password=args.password)
else:
    openreview = Client(baseurl=args.baseurl)
baseurl = openreview.baseurl

submissions = openreview.get_notes(invitation='NIPS.cc/2016/workshop/NAMPI/-/submission')

def single_assignment_valid(s):
    try:    
        reviewer = s.split(',')[0]
        paper_number = s.split(',')[1]

        try: 
            int(paper_number)
        except ValueError:
            return False

        if not '@' in reviewer:
            return False

        return True
    except IndexError:
        return False

def assign_reviewer(reviewer,paper_number):
    notes = [note for note in submissions if str(note.number)==str(paper_number)]
    if notes:
        conflicts = [note.content['conflicts'] for note in notes]
        conflict_list = []
        if conflicts:
            for c in conflicts[0].split(';'):
                if str(c.strip()):
                    conflict_list.append(str(c.strip()))
        if 'authorids' in note.content:
            conflict_list.append(note.content['authorids'])

        reviewer_group = get_reviewer_group(reviewer, paper_number, conflict_list)
        reviewer_group_id = str(reviewer_group.id)
        print "Assigned reviewer", reviewer_group_id
    else:
        print "Paper number " + paper_number + " does not exist" 


def create_reviewer_group(new_reviewer_id, reviewer, paper_number, conflict_list):
    print 'Creating reviewer: ', new_reviewer_id
    new_reviewer = Group(
        new_reviewer_id,
        signatures=['NIPS.cc/2016/workshop/NAMPI'],
        writers=['NIPS.cc/2016/workshop/NAMPI'],
        members=[reviewer],
        readers=['NIPS.cc/2016/workshop/NAMPI','NIPS.cc/2016/workshop/NAMPI/pcs',new_reviewer_id],
        nonreaders=conflict_list,
        signatories=[new_reviewer_id])
    openreview.post_group(new_reviewer)
    return new_reviewer
    

def get_reviewer_group(reviewer, paper_number, conflict_list):
    
    reviewers = openreview.get_group('NIPS.cc/2016/workshop/NAMPI/paper'+paper_number+'/reviewers')
    existing_reviewers = reviewers.members

    conference_reviewers = openreview.get_group('NIPS.cc/2016/workshop/NAMPI/reviewers')
    conference_reviewers_invited = openreview.get_group('NIPS.cc/2016/workshop/NAMPI/reviewers-invited')

    if not (reviewer in conference_reviewers_invited.members):
        print "WARNING: You have not sent an email invitation to user ",reviewer," asking whether or not they would like to participate."
        cont = raw_input("Would you like to continue? (y/n) [default: NO] ")
        if cont.lower()!='y' and cont.lower()!='yes':
            print "Aborting"
            sys.exit()
        openreview.post_group(conference_reviewers_invited.add_member(reviewer))

    if not (reviewer in conference_reviewers.members):
        openreview.post_group(conference_reviewers.add_member(reviewer))
    
    for r in existing_reviewers:
        existing_reviewer = openreview.get_group(r)
        if hasattr(existing_reviewer,'members'):
            if reviewer in existing_reviewer.members:
                print "Reviewer " + reviewer + " found in " + existing_reviewer.id
                return existing_reviewer
    new_reviewer_id = 'NIPS.cc/2016/workshop/NAMPI/paper'+str(paper_number)+'/reviewer'+str(len(existing_reviewers)+1)
    new_reviewer = create_reviewer_group(new_reviewer_id, reviewer, paper_number, conflict_list)
    openreview.post_group(reviewers.add_member(new_reviewer.id))
    return new_reviewer


##################################################################


if args.assignments.endswith('.csv'):   
    with open(args.assignments, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            reviewer = row[0]
            paper_number = row[1]
            assign_reviewer(reviewer,paper_number)
elif single_assignment_valid(args.assignments):
    reviewer = args.assignments.split(',')[0]
    paper_number = args.assignments.split(',')[1]
    assign_reviewer(reviewer,paper_number)
else:
    print "Invalid input"
    sys.exit()
