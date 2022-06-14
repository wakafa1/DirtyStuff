from datetime import datetime
import os
import sys
import os.path as osp

import load_balance as lb
from common import local_config as lc
from cptdesc import CptBatchDescription
from emutasks import EmuTasksConfig

# `emu` 自动化测试

debug = False
num_threads = 80

ver = '06'
# exe = f'/bigdata/ljw/xs-emus/emu'
exe = f'/nfs/home/goulingrui/emu-0609'
data_dir = f'{lc.cpt_top}/spec{ver}_rv64gcb_o2_20m/take_cpt/' # cpt dir
top_output_dir = '/nfs/home/goulingrui/expri_results/' # output dir
simpoints_file = f'{lc.cpt_top}/spec{ver}_rv64gcb_o2_20m/json/simpoint_summary.json'

workload_filter = []

# simpoints_file = lc.simpoints_file[ver]

cpt_desc = CptBatchDescription(data_dir, exe, top_output_dir, ver,
        is_simpoint=True,
        is_uniform=False,
        simpoints_file=simpoints_file)

parser = cpt_desc.parser

parser.add_argument('-t', '--debug-tick', action='store', type=int)
parser.add_argument('-C', '--config', action='store', type=str)

args = cpt_desc.parse_args()

date = datetime.now().strftime('%Y-%m-%d')
CurConf = EmuTasksConfig
task_name = f'xs_simpoint_batch/SPEC{ver}_{CurConf.__name__}_{date}'
cpt_desc.set_task_filter()
cpt_desc.set_conf(CurConf, task_name)
cpt_desc.filter_tasks(hashed=True, n_machines=3)

debug_tick = None

if args.debug_tick is not None:
    debug_tick = args.debug_tick
    debug_flags = frontend_flags + backend_flags


for task in cpt_desc.tasks:
    task.sub_workload_level_path_format()
    task.set_trivial_workdir()
    task.avoid_repeat = True

    task.add_direct_options([])
    task.add_dict_options({
        '-W': str(20*10**6),
        '-I': str(40*10**6),
        '-i': task.cpt_file,
        # '--gcpt-restorer': '/home/zyy/projects/NEMU/resource/gcpt_restore/build/gcpt.bin',
        # '--gcpt-warmup': str(50*10**6),
    })
    task.format_options(space=True)
print(f'Output dir {top_output_dir}/{task_name}')
print(len(cpt_desc.tasks))

cpt_desc.set_numactl(selected_cores=list(range(0, num_threads)))
# exit()
cpt_desc.run(lb.get_machine_threads(), debug)

