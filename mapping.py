#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Osman Baskaya"


import sys
from collections import defaultdict as dd
from random import shuffle
import numpy as np
from sklearn.preprocessing import normalize


def chunks(l, n):
    """ Yield successive n-sized chunks from l. """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def load_key(fname):

    d = dd(lambda: dd(lambda: dd(lambda : 0.)))

    lines = open(fname).readlines()
    #c = 0
    for line in lines:
        line = line.split()
        key, inst = line[:2]
        senses = line[2:]
        senses = [sense.split('/')  for sense in senses]
        if len(senses) == 1:
            #c += 1
            d[key][inst][senses[0][0]] = 1.
        else:
            uni = []
            for sense in senses:
                if len(sense) == 1:
                    uni.append(sense)
                else:
                    d[key][inst][sense[0]] = sense[1]
            if len(uni) > 0:
                assert len(uni) != len(senses), "Some sense weighted, some not: %s" % inst
                val = 1. / len(uni)
                for sense in senses:
                    d[key][inst][sense[0]] = val
            
    #print c
    return d


def remap(gold_instances, test_instances, training_instances):
    #print len(training_instances),  len(test_instances.keys()), len(gold_instances)
    test_ids = []
    gold_ids = []
    for instance_id in training_instances:
        gs_perception = gold_instances[instance_id]
        ts_perception = test_instances[instance_id]
        if not (gs_perception is None or ts_perception is None):
            test_ids.extend(ts_perception.keys())
            gold_ids.extend(gs_perception.keys())

    m = len(test_ids)
    n = len(gold_ids)
    if m != 0 and n != 0:
        test_sense_ids = dict(zip(test_ids, range(m)))
        gold_sense_ids = dict(zip(gold_ids, range(n)))

        mapping_matrix = np.zeros([m, n])
    
        for instance_id in training_instances:
            gs_perception = gold_instances[instance_id]
            ts_perception = test_instances[instance_id]
            
            for key, val in ts_perception.iteritems():
                ts_ind = test_sense_ids[key]
                for gold_key, gold_val in gs_perception.iteritems():
                    gs_ind = gold_sense_ids[gold_key]
                    score = gold_val * val
                    mapping_matrix[ts_ind, gs_ind] += score

        # Normalize the matrix
        mapping_matrix = normalize(mapping_matrix, norm='l1', axis=1)

        test_inst_ids = set(test_instances.keys()).difference(training_instances)

        remapped = dict()

        for test_inst_id in test_inst_ids:
            test_vector = np.zeros(m)
            ts_perception = test_instances[test_inst_id]
            for key, col in test_sense_ids.iteritems():
                if key in ts_perception:
                    test_vector[col] = ts_perception[key]

    
            result = np.dot(test_vector, mapping_matrix)
            remapped_perception = dict()

            for i, score in enumerate(result):
                if score > 0:
                    gg = None
                    for gs, val in gold_sense_ids.iteritems():
                        if val == i:
                            gg = gs
                            break
                    if gg is None:
                        raise ValueError, "Unmapped: {} in {}".format(i, gold_sense_ids)
                    remapped_perception[gg] = score
            if len(remapped_perception) > 0:
                remapped[test_inst_id] = remapped_perception

        return remapped
    
def convert(goldkey, testkey, training_instances, one_sense=True):
    outputKey = dict()
    for key in goldkey.keys():
        related_instances = ([i for i in training_instances if i.startswith(key)])
        remapped_instances = remap(goldkey[key], testkey[key], related_instances)
        outputKey[key] = remapped_instances

    if one_sense:
        for key, val in outputKey.iteritems():
            for k, v in val.iteritems():
                removing_sense = sorted(v, key=lambda x: v[x], reverse=True)[1:]
                if len(removing_sense) > 0:
                    for sense in removing_sense:
                        v.pop(sense)

    return outputKey



def run_eval(goldkey, testkey, test_sets, all_instances):
    
    all_instances = set(all_instances)
    for test_instances in test_sets:
        training_instances = all_instances.difference(test_instances)
        remapped_testkey = convert(goldkey, testkey, training_instances)
        print remapped_testkey
        


#goldkey = load_key(sys.argv[1])
#testkey = load_key(sys.argv[2])
goldkey = load_key('all.singlesense.key')
testkey = load_key('induced.ans')

#k = sorted(goldkey.values()[0].keys(), key=lambda x: int(x.split('.')[-1]))

all_instances = []
for inst in goldkey.values():
    all_instances.extend(sorted(inst.keys(), key=lambda x: int(x.split('.')[-1])))
shuffle(all_instances)

test_sets = list(chunks(all_instances, len(all_instances) / 5))

# if division not exact
if len(test_sets) == 6:
    test_sets[4].extend(test_sets[5])
    test_sets.pop()

test_sets = [set(t) for t in test_sets]
run_eval(goldkey, testkey, test_sets, all_instances)

def main():
    pass

if __name__ == '__main__':
    main()

