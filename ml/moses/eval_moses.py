import subprocess
import re
import os.path
import argparse
import tempfile
import shlex
import pandas
from data_util.util import compute_metrics, dtype
from collections import defaultdict


def convert_out(moses_out_path, dest):
    """
    stript cost from moses stdout and write to dest top 10 programs
    """
    i = 0
    with open(os.path.expanduser(moses_out_path), 'rt') as f:
        for line in f:
            dest.write(re.match('^.\d+?\s(.+?)\s+?\n?$', line).group(1) + '\n')
            i += 1
            if i == 10:
                break
    dest.flush()


def estimate(program_path, out_path, csv_path, target_field='posOutcome'):
    if out_path:
        tmp = tempfile.NamedTemporaryFile(mode='w+t')
        convert_out(out_path, tmp)
        program_path = tmp.name

    line = "aseval-table -i {0} -C {1} -u {2} --labels=1".format(csv_path,
            program_path, target_field)

    out = subprocess.run(shlex.split(line), stdout=subprocess.PIPE)
    # split by target variable
    splitted = [x for x in out.stdout.decode().split(target_field) if bool(x)]
    result = list()
    for line in splitted:
        estimated = [int(x) for x in line.split()]
        result.append(estimated)
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate combo program on \
            train and validation tables')
    parser.add_argument('--train-path',
                        help="path to train csv file")
    parser.add_argument('--validation-path',
                        help="path to validation csv file")
    parser.add_argument('--out-file', default='',
                        help="path to moses a file with moses output")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    val_path = args.validation_path
    train_path = args.train_path
    moses_out_path = args.out_file
    results = evaluate_moses(train_path, val_path, moses_out_path)
    for i, result in results.items():
        print('program #{0}'.format(i))
        for k, v in result.items():
            print(k, v)

def evaluate_moses(train_path, val_path, moses_out_path, target='posOutcome'):
    # load averaged treatment table
    val_data = pandas.read_csv(val_path, dtype=dtype)
    train_data = pandas.read_csv(train_path, dtype=dtype)
    val_est_list = estimate('', moses_out_path, val_path, target_field=target)
    train_est_list = estimate('', moses_out_path, train_path, target_field=target)

    results = dict()
    i = 0
    for val_est, train_est in zip(val_est_list, train_est_list):
        i += 1
        result = defaultdict(list)
        compute_metrics(result, val_data[target].to_list(), val_est,
                train_data[target].to_list(), train_est)
        results[i] = result
    return results

if __name__ == '__main__':
    main()
