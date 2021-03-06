import random
import string
import threading
import time
from collections import namedtuple

from numpy import mean

from service.client import BertClient
from service.server import BertServer


class BenchmarkClient(threading.Thread):
    def __init__(self, args):
        super().__init__()
        self.batch = [''.join(random.choices(string.ascii_uppercase + string.digits,
                                             k=args.client_seq_len)) for _ in args.client_batch_size]

        self.bc = BertClient()
        self.num_repeat = args.num_repeat
        self.avg_time = 0

    def run(self):
        time_all = []
        for _ in range(self.num_repeat):
            start_t = time.clock()
            self.bc.encode(self.batch)
            time_all.append(time.clock() - start_t)
        self.avg_time = mean(time_all)


if __name__ == '__main__':
    common = {
        'model_dir': '/data/cips/save/chinese-bert/chinese_L-12_H-768_A-12/',
        'num_worker': 8,
        'num_repeat': 5,
        'port': 5555
    }
    experiments = [
        {
            'max_seq_len': [20, 40, 80, 100],
            'batch_size_per_worker': 128,
            'client_batch_size': 2048,
            'client_seq_len': 100,
            'num_client': 1
        },
        {
            'max_seq_len': 20,
            'batch_size_per_worker': [64, 128, 256, 512],
            'client_batch_size': 2048,
            'client_seq_len': 100,
            'num_client': 1
        },
        {
            'max_seq_len': 20,
            'batch_size_per_worker': 128,
            'client_batch_size': [64, 256, 1024, 2048],
            'client_seq_len': 100,
            'num_client': 1,
        },
        {
            'max_seq_len': 20,
            'batch_size_per_worker': 128,
            'client_batch_size': 2048,
            'client_seq_len': 100,
            'num_client': [1, 2, 3, 4],
        },
    ]

    # exp1
    exp = experiments[0]
    var_name = 'max_seq_len'
    for var in exp[var_name]:
        args = namedtuple('args', ','.join(list(common.keys()) + list(exp.keys())))
        for k, v in common.items():
            setattr(args, k, v)
        for k, v in exp.items():
            setattr(args, k, v)
        # override the var_name
        setattr(args, var_name, var)

        print('will start a sever with args: %s' % args)
        server = BertServer(args)
        server.start()

        for _ in range(args.num_client):
            bc = BenchmarkClient(args)
            bc.start()
            bc.join()
            print('time used: %.3f' % bc.avg_time)
        server.join()
